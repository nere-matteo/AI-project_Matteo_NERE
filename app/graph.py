"""The application approval gate for an externally visible action."""

from __future__ import annotations

import json
import sys
from getpass import getuser
from select import select
from typing import TypedDict
from uuid import uuid4

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from project.trace import repo_root

APPROVAL_TIMEOUT_SECONDS = 30.0


class ApprovalState(TypedDict, total=False):
    payload: dict
    decision: dict


def _submit(state: ApprovalState) -> dict:
    """Wait for a verdict before the caller can submit."""
    return {"decision": interrupt(state["payload"])}


def _read_decision(payload: dict) -> dict:
    print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
    print(
        f'Approval required ({APPROVAL_TIMEOUT_SECONDS:g}s). Enter approve, '
        'reject, or edit {"field":"value"}: ',
        end="", file=sys.stderr, flush=True,
    )
    ready, _, _ = select([sys.stdin], [], [], APPROVAL_TIMEOUT_SECONDS)
    if not ready:
        print(file=sys.stderr)
        return {"verdict": "timeout", "by": "approval-timeout"}
    line = sys.stdin.readline()
    if not line:
        return {"verdict": "timeout", "by": "no-input"}

    verdict, _, edit = line.strip().partition(" ")
    by = getuser()
    if verdict == "edit":
        try:
            edits = json.loads(edit)
            if not isinstance(edits, dict) or not edits or edits.keys() - payload["arguments"].keys():
                raise ValueError("edit must name an existing field")
        except ValueError:
            print("Invalid edit. The submission was held.", file=sys.stderr)
            return {"verdict": "reject", "by": by}
        return {"verdict": "edit", "by": by,
                "arguments": {**payload["arguments"], **edits}}
    return {"verdict": "approve" if verdict == "approve" and not edit else "reject",
            "by": by}


def request_approval(payload: dict, unattended: bool = False) -> dict:
    """Return a local review decision, or hold an unanswered submission."""
    if unattended or not sys.stdin.isatty():
        return {"verdict": "timeout", "by": "unattended" if unattended else "no-terminal"}

    path = repo_root() / "artifacts" / "app_approvals.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": uuid4().hex}}
    graph = StateGraph(ApprovalState)
    graph.add_node("submit", _submit)
    graph.add_edge(START, "submit")
    graph.add_edge("submit", END)

    with SqliteSaver.from_conn_string(str(path)) as saver:
        gate = graph.compile(checkpointer=saver)
        paused = gate.invoke({"payload": payload}, config)
        decision = _read_decision(paused["__interrupt__"][0].value)
        return gate.invoke(Command(resume=decision), config)["decision"]
