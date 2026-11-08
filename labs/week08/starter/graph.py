"""The pipeline as a graph, with one gated step. TODO 3 to 5.

Four nodes. Three of them execute automatically and one stops and asks a
human, and which one is a decision about consequence rather than about
confidence.
"""

from __future__ import annotations

from math import isfinite
from typing import Annotated, TypedDict

from faults import ContractDrift, FaultPlan
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from retry import StepPolicy, call_with_policy

import tools


def append(a: list, b: list) -> list:
    return a + b


class CaseState(TypedDict):
    case_id: str
    topic: str
    passages: list[str]
    fee: dict
    draft: str
    submitted: bool
    decision: str
    approval: dict
    degraded: bool
    missing: Annotated[list[str], append]
    events: Annotated[list[str], append]
    side_effects: Annotated[list[str], append]


SEARCH_POLICY = StepPolicy(attempts=3, base_delay=0.05, jitter=True,
                           max_elapsed=3.0, on_exhausted="degrade")
FEES_POLICY = StepPolicy(attempts=3, base_delay=0.05, jitter=True,
                         max_elapsed=3.0, on_exhausted="degrade")


def validate_fee(value) -> None:
    """TODO 4. Where contract drift is caught.

    Drift is the fault no retry fixes, because the call succeeded. The only
    thing that catches it is a check on the SHAPE of what came back, run on
    the success path. If you have no validation, a renamed field flows all
    the way to the answer and the run reports success.
    """
    if not isinstance(value, dict):
        raise ContractDrift("fee response must be an object")
    if not value:
        return  # An empty lookup is valid and handled as missing in price.
    amount = value.get("fee_eur")
    period = value.get("period")
    if (
        type(amount) not in (int, float)
        or (isinstance(amount, float) and not isfinite(amount))
        or amount < 0
        or not isinstance(period, str)
        or not period.strip()
    ):
        raise ContractDrift("expected a nonnegative fee_eur and a period")


def validate_passages(value) -> None:
    if not isinstance(value, list) or any(
        not isinstance(passage, str) or not passage.strip() for passage in value
    ):
        raise ContractDrift("expected a list of search passages")


# --------------------------------------------------------------------------
# TODO 3. The nodes, each with its own policy.
# --------------------------------------------------------------------------

def gather(state: CaseState, plan: FaultPlan) -> dict:
    """TODO 3a. Search, with retries and a fallback.

    Three cases, and the middle one is the interesting one:

      the call failed after everything    -> degraded, say search is down
      the call SUCCEEDED and returned []  -> decide, and be able to defend it
      the call succeeded with passages    -> note if the fallback was used

    An empty result is not an error and it is not a success either. It is
    the tool saying it does not cover this. Treating it as a success is how
    a pipeline answers a question from nothing.

    Record what is absent in `missing` so `draft` can say it out loud, and
    append to `events` so the checkpoint has something to count.
    """
    result = call_with_policy(
        tools.search, plan, state["topic"], policy=SEARCH_POLICY,
        fallback=tools.keyword_fallback, validate=validate_passages,
    )
    passages = result.value or []
    outcome = "empty" if result.ok and not passages else result.outcome
    return {
        "passages": passages,
        "missing": [] if passages else ["handbook evidence"],
        "events": [f"search:{outcome}:attempts={result.tries}"],
    }


def price(state: CaseState, plan: FaultPlan) -> dict:
    """TODO 3b. The fee lookup, passing `validate_fee` to the policy.

    This is the step contract drift hits. Without a validator the renamed
    field flows into the answer and the run reports success.
    """
    result = call_with_policy(
        tools.fees, plan, state["topic"], policy=FEES_POLICY,
        validate=validate_fee,
    )
    fee = result.value or {}
    outcome = "empty" if result.ok and not fee else result.outcome
    return {
        "fee": fee,
        "missing": [] if fee else ["verified fee"],
        "events": [f"fees:{outcome}:attempts={result.tries}"],
    }


def draft(state: CaseState) -> dict:
    """TODO 5. The goal predicate, and what a partial answer says.

    A degraded answer must name what is missing IN THE TEXT THE USER READS.
    An answer that quietly omits the fee is indistinguishable from one where
    there was no fee, and the reader has no way to know which they got.

    A degrade path that returns an empty string is technically graceful and
    completely useless.
    """
    parts = list(state["passages"])
    fee = state["fee"]
    if fee:
        parts.append(f"Verified fee: EUR {fee['fee_eur']:.2f} per {fee['period']}.")

    missing = set(state["missing"])
    if not state["passages"]:
        missing.add("handbook evidence")
    if not fee:
        missing.add("verified fee")
    if missing:
        parts.append("I couldn't confirm the following: " + ", ".join(sorted(missing)) + ".")

    return {"draft": "\n".join(parts), "degraded": bool(missing)}


def submit(state: CaseState) -> dict:
    """Pause the only operation that can submit a case."""
    original = {"topic": state["topic"], "fee": state["fee"]}
    decision = interrupt({
        "action": "submit_case",
        "case_id": state["case_id"],
        "arguments": original,
        "evidence": state["passages"],
        "degraded": state["degraded"],
        "missing": sorted(set(state["missing"])),
    })

    if not isinstance(decision, dict):
        decision = {}
    verdict = decision.get("verdict")
    by = decision.get("by")
    if verdict not in ("approve", "edit", "reject") or not isinstance(by, str) or not by.strip():
        verdict, by = "reject", "invalid approval"

    arguments = original.copy()
    if verdict == "edit":
        edits = decision.get("arguments")
        try:
            if not isinstance(edits, dict) or not edits or edits.keys() - original.keys():
                raise ValueError("expected an edit to topic or fee")
            if "topic" in edits:
                topic = edits["topic"]
                if not isinstance(topic, str) or not topic.strip():
                    raise ValueError("topic must be nonempty text")
                arguments["topic"] = topic
            if "fee" in edits:
                if not isinstance(edits["fee"], dict) or not edits["fee"]:
                    raise ValueError("fee edit must include a field")
                arguments["fee"] = {**original["fee"], **edits["fee"]}
                validate_fee(arguments["fee"])
        except (ValueError, ContractDrift):
            verdict = "reject"

    submitted = verdict in ("approve", "edit")
    changes = {
        field: {"before": original[field], "after": value}
        for field, value in arguments.items()
        if submitted and value != original[field]
    }
    approval = {
        "case_id": state["case_id"],
        "verdict": verdict,
        "by": by,
        "submitted": submitted,
        "decision": verdict,
        "original_arguments": original,
        "arguments": arguments if submitted else None,
        "changes": changes,
        "evidence": state["passages"],
    }
    update = {
        "submitted": submitted,
        "decision": verdict,
        "approval": approval,
        "events": [f"gate:{verdict}:{by}"],
    }
    if submitted:
        update.update(arguments)
        update["side_effects"] = [f"SUBMITTED {state['case_id']}"]
    return update


def build(plan: FaultPlan, saver):
    graph = StateGraph(CaseState)
    graph.add_node("gather", lambda s: gather(s, plan))
    graph.add_node("price", lambda s: price(s, plan))
    graph.add_node("draft", draft)
    graph.add_node("submit", submit)
    graph.add_edge(START, "gather")
    graph.add_edge("gather", "price")
    graph.add_edge("price", "draft")
    graph.add_edge("draft", "submit")
    graph.add_edge("submit", END)
    return graph.compile(checkpointer=saver)


def initial(case_id: str, topic: str) -> CaseState:
    return {"case_id": case_id, "topic": topic, "passages": [], "fee": {},
            "draft": "", "submitted": False, "decision": "", "approval": {},
            "degraded": False, "missing": [], "events": [],
            "side_effects": []}
