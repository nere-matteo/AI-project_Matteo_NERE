"""Blocks 1 and 2. Break it, then survive it. TODO 6.

    python 01_survive.py --baseline     # no policy at all, watch it die
    python 01_survive.py                # the full fault matrix, hardened

No model is called anywhere in this file. The tools are offline and the
faults are deterministic, so the whole block runs in about a second and the
same seed gives the same failures every time.

The written answer is at the bottom.
"""

from __future__ import annotations

import argparse

from faults import FAULTS, FaultPlan, RateLimited, ServerError, ToolTimeout
from retry import Attempt, StepPolicy, StepResult, call_with_policy

import tools
from graph import draft, initial, validate_fee, validate_passages

from project.trace import TraceRecorder, local_conditions, write_json

HARDENED = StepPolicy(attempts=3, base_delay=0.02, jitter=True,
                      max_elapsed=3.0, on_exhausted="degrade")


def call_once(fn, *args, **_policy_options) -> StepResult:
    """Record the raw result of one call so the baseline can score all faults."""
    try:
        value = fn(*args)
    except (ToolTimeout, RateLimited, ServerError) as exc:
        return StepResult(attempts=[Attempt(1, type(exc).__name__)],
                          outcome="escalated")
    return StepResult(value=value, ok=True, attempts=[Attempt(1, None)])


def run_one(kind: str, hardened: bool) -> dict:
    """One fault, against search and against fees, with or without policy."""
    call = call_with_policy if hardened else call_once
    plan = FaultPlan.parse(f"search:{kind}@1.0,fees:{kind}@1.0", seed=42)

    rec = TraceRecorder(
        week=8, case_id=f"{kind}-{'hardened' if hardened else 'baseline'}",
        conditions=local_conditions("none (offline tools)", temperature=0.0,
                                    fault=kind, policy=HARDENED.attempts if hardened else 1),
        user_input=f"fault={kind}")

    with rec.step("tool", "search") as span:
        search = call(
            tools.search, plan, "parking vignette", policy=HARDENED,
            fallback=tools.keyword_fallback if hardened else None,
            validate=validate_passages if hardened else None)
        span.ok = search.ok
        span.detail(tries=search.tries, outcome=search.outcome,
                    attempts=[vars(attempt) for attempt in search.attempts],
                    used_fallback=search.used_fallback,
                    fallback_error=search.fallback_error)

    with rec.step("tool", "fees") as span:
        fee = call(
            tools.fees, plan, "parking vignette", policy=HARDENED,
            validate=validate_fee if hardened else None)
        span.ok = fee.ok
        span.detail(tries=fee.tries, outcome=fee.outcome,
                    attempts=[vars(attempt) for attempt in fee.attempts],
                    used_fallback=fee.used_fallback,
                    fallback_error=fee.fallback_error)

    # Classify the OUTCOME, not merely whether something came back.
    #
    # "Did it answer" is the obvious metric and it is a trap: it counts a
    # confidently wrong answer as a success, and so it rewards the pipeline
    # with no validation. Ask instead which of four things happened.
    TRUE_FEE = 60.0
    got_fee = fee.value.get("fee_eur") if isinstance(fee.value, dict) else None
    has_passage = bool(search.value)

    if has_passage and got_fee == TRUE_FEE:
        verdict = "correct"          # right answer, from good data
    elif has_passage and got_fee is not None:
        verdict = "WRONG"            # answered, and the number is not right
    elif not has_passage and not got_fee:
        verdict = "failed"           # nothing at all, and it said so
    else:
        verdict = "degraded"         # partial, and it names what is missing

    answer = None
    if hardened:
        state = initial("fault-matrix", "parking vignette")
        state["passages"] = search.value or []
        state["fee"] = fee.value or {}
        answer = draft(state)["draft"]

    rec.finish(output=answer,
               outcome={"correct": "ok", "WRONG": "error",
                        "degraded": "degraded", "failed": "error"}[verdict],
               fault=kind, hardened=hardened, verdict=verdict)

    return {"fault": kind, "hardened": hardened,
            "search_tries": search.tries, "search_outcome": search.outcome,
            "fees_tries": fee.tries, "fees_outcome": fee.outcome,
            "verdict": verdict, "answer": answer}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", action="store_true",
                    help="no retries, no fallback, no validation")
    args = ap.parse_args()
    hardened = not args.baseline

    print(f"{'fault':<14}{'search':>20}{'fees':>20}{'verdict':>12}")
    print("-" * 70)
    rows = []
    for kind in FAULTS:
        row = run_one(kind, hardened)
        rows.append(row)
        print(f"{kind:<14}"
              f"{row['search_outcome'] + ' x' + str(row['search_tries']):>20}"
              f"{row['fees_outcome'] + ' x' + str(row['fees_tries']):>20}"
              f"{row['verdict']:>12}")

    tally = {v: sum(1 for r in rows if r["verdict"] == v)
             for v in ("correct", "WRONG", "degraded", "failed")}
    label = "hardened" if hardened else "BASELINE, no policy"
    print(f"\n  {label}: correct {tally['correct']}, "
          f"WRONG {tally['WRONG']}, degraded {tally['degraded']}, "
          f"failed {tally['failed']}  (out of {len(rows)})")
    print("  The number that matters is WRONG: an answer that is confidently")
    print("  incorrect is worse than one that admits it is incomplete.")
    write_json(f"artifacts/week08_faults_"
               f"{'hardened' if hardened else 'baseline'}.json",
               {"rows": rows})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
