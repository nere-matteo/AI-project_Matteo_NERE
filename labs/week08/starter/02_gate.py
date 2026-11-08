"""Block 3. The gate, and what the state will not tell you. TODO 7.

Run it as TWO separate invocations. That is the whole exercise: if the pause
only survives inside one script, it is a session variable with extra steps.

    python 02_gate.py start
    python 02_gate.py resume approve      # or reject, or edit

SQLite keeps the paused run and the final approval decision.
"""

from __future__ import annotations

import argparse

from faults import FaultPlan
from graph import build, initial
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from project.trace import repo_root, write_json

DB = repo_root() / "artifacts" / "week08_runs.sqlite"
CASE = "RB-2026-0042"


def show(graph, cfg) -> None:
    snap = graph.get_state(cfg)
    print(f"    next node:     {snap.next}")
    print(f"    side effects:  {snap.values.get('side_effects')}")
    print(f"    events:        {snap.values.get('events')}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", nargs="?", choices=("start", "resume"),
                        default="start")
    parser.add_argument("verdict", nargs="?", choices=("approve", "reject", "edit"))
    args = parser.parse_args()
    if args.mode == "start" and args.verdict is not None:
        parser.error("a verdict can only be supplied when resuming")
    if args.mode == "resume" and args.verdict is None:
        parser.error("resume requires approve, reject, or edit")
    cfg = {"configurable": {"thread_id": CASE}}
    plan = FaultPlan.parse("")          # no faults, the gate is the subject

    DB.parent.mkdir(parents=True, exist_ok=True)

    with SqliteSaver.from_conn_string(str(DB)) as saver:
        graph = build(plan, saver)

        if args.mode == "start":
            if graph.get_state(cfg).next:
                raise SystemExit("A case is already paused. Resume it first.")
            saver.delete_thread(CASE)
            out = graph.invoke(initial(CASE, "parking vignette"), cfg)
            payload = out["__interrupt__"][0].value
            print("  the run has PAUSED at the gate\n")
            print(f"    action:    {payload['action']}")
            print(f"    arguments: {payload['arguments']}")
            print(f"    evidence:  {payload['evidence']}")
            print(f"    degraded:  {payload['degraded']}")
            show(graph, cfg)
            print("\n  This process can now exit, or be killed. Then run:")
            print("    python starter/02_gate.py resume approve")
            return 0

        before = graph.get_state(cfg)
        if not before.next:
            raise SystemExit("Nothing is paused. Run `start` first.")
        print(f"  resuming a run this process did not create")
        print(f"    it was paused before: {before.next}\n")

        resume = {"verdict": args.verdict, "by": "a.muller"}
        if args.verdict == "edit":
            # The approver's most common response is neither approve nor
            # reject: it is approve with one field changed. A gate with no
            # edit path throws away correct work and trains the approver to
            # approve rather than to correct.
            resume["arguments"] = {"fee": {"fee_eur": 55.0}}

        out = graph.invoke(Command(resume=resume), cfg)
        print(f"    submitted: {out.get('submitted')}")
        print(f"    decision:  {out.get('decision')}")
        print(f"    fee now:   {out.get('fee')}")
        show(graph, cfg)

        record = {**out["approval"], "events": out["events"]}
        print(f"    reviewer:  {record['by']}")
        print(f"    changes:   {record['changes']}")
        write_json("artifacts/week08_approval.json", record)
        print("\n  decision record written to artifacts/week08_approval.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
