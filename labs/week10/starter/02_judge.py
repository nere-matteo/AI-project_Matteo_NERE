"""Block 2: a judge, validated against labels you wrote first.

Three steps, in this order, and the order is the argument:

  1. label     twelve cases by hand, before any judge runs
  2. judge     score the same twelve
  3. sweep     vary the threshold and watch agreement move

Step 3 is the one that matters. A judge is not a model, it is a model AND a
threshold, and reporting the first without the second describes half an
instrument.

    python 02_judge.py --replay     # the recorded judgments, instant
    python 02_judge.py              # live, about fifty seconds
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project_spine"))

import judge as J  # noqa: E402

from project.trace import write_json  # noqa: E402

SWEEP = [0.15, 0.25, 0.35, 0.45, 0.50, 0.55, 0.65, 0.75, 0.85]


def collect(replay: bool) -> dict[str, J.Judgment]:
    path = J.fixture_path() if replay else J.LIVE_JUDGMENTS
    recorded = J.load_recorded(path)
    print(f"Judge scores: {path}", flush=True)
    pending = [case for case in J.LABELS if case.case_id not in recorded]
    if replay and pending:
        missing = ", ".join(case.case_id for case in pending)
        raise SystemExit(f"Missing scores for {missing}. Run 02_judge.py live.")
    if not pending:
        print("Using recorded scores (zero new model calls).")
        return recorded

    print(f"Live scoring with {J.MODEL}, DeepEval {version('deepeval')}", flush=True)
    metric = J.build_metric()
    for case in pending:
        judgment = J.judge_one(metric, case)
        recorded[case.case_id] = judgment
        J.save_recorded(recorded)
        print(f"  {case.case_id} {judgment.verdict:<5} "
              f"{judgment.score:.2f} ({judgment.seconds}s)", flush=True)
    return recorded


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true",
                    help="read local judgments, or use the course fixture if absent")
    args = ap.parse_args()

    judgments = collect(args.replay)
    agreement = J.validate(judgments)

    print(f"\nJUDGE AGAINST HAND LABELS, threshold {J.THRESHOLD}\n")
    print(f"{'case':<7}{'human':>7}{'judge':>7}{'score':>7}   why the human said so")
    print("-" * 76)
    for row in agreement.rows:
        flag = "" if row["human"] == row["judge"] else "  <-- DISAGREE"
        print(f"{row['case_id']:<7}{row['human']:>7}{row['judge']:>7}"
              f"{row['score']:>7.2f}   {row['why_human'][:32]:<34}{flag}")
    print(f"\n  agreement {agreement.agreed}/{agreement.n} = "
          f"{agreement.rate:.2f}   {agreement.confusion()}")

    print(f"\nTHE SAME JUDGMENTS AT OTHER THRESHOLDS\n")
    print(f"{'threshold':>10}{'agreement':>11}{'false_pass':>12}"
          f"{'false_fail':>12}")
    print("-" * 47)
    sweep_rows = []
    for threshold in SWEEP:
        measured = J.validate(judgments, threshold)
        confusion = measured.confusion()
        false_pass = confusion["false_pass"]
        false_fail = confusion["false_fail"]
        sweep_rows.append({"threshold": threshold, "agreement": measured.rate,
                           "false_pass": false_pass, "false_fail": false_fail})
        print(f"{threshold:>10.2f}{measured.rate:>11.2f}{false_pass:>12}"
              f"{false_fail:>12}")

    highest_fail = max(r["score"] for r in agreement.rows if r["human"] == "fail")
    lowest_pass = min(r["score"] for r in agreement.rows if r["human"] == "pass")
    if highest_fail < lowest_pass:
        print(f"\nPerfect agreement for {highest_fail:g} < threshold <= {lowest_pass:g}.")
    else:
        print("\nNo threshold separates all human passes from all human failures.")

    total = sum(r["seconds"] for r in agreement.rows)
    print(f"\nRecorded scoring time: {total:.2f}s for {agreement.n} cases "
          f"({total / agreement.n:.2f}s per case).")

    write_json("artifacts/week10_judge.json",
               {"threshold": J.THRESHOLD, "rows": agreement.rows,
                "source": "local" if J.fixture_path() == J.LIVE_JUDGMENTS else "reference",
                "confusion": agreement.confusion(), "sweep": sweep_rows,
                "highest_human_fail_score": highest_fail,
                "lowest_human_pass_score": lowest_pass})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
