"""Block 1: everything you can measure for zero model calls.

Your project has been writing traces since week 2. This reads them back and
computes five numbers per week, none of which costs a token. Run it before
you write a single judge, because most of what people reach for a judge to
measure is already sitting in their own logs.

    python 01_free.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project_spine"))

from dimensions import report  # noqa: E402
from loader import load_traces, source_of, traces_path  # noqa: E402

from project.trace import write_json  # noqa: E402

WEEKS = [5, 8, 9]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, default=None)
    args = ap.parse_args()

    if args.week is not None:
        traces = load_traces(args.week)
        for source in sorted({source_of(t) for t in traces}):
            group = [t for t in traces if source_of(t) == source]
            print(f"WEEK {args.week} ({source}), {len(group)} traces\n")
            for d in report(group):
                print("  " + d.line())
        if not traces:
            print(f"WEEK {args.week}: no traces")
        return 0

    start = perf_counter()
    everything = load_traces()
    names = ["accuracy", "consistency", "robustness", "predictability",
             "safety"]
    print(f"THE FREE LAYER, {len(everything)} recorded runs, zero model calls\n")
    print(f"{'week':<7}{'runs':>6}" + "".join(f"{n:>16}" for n in names))
    print("-" * 93)
    groups = {week: [t for t in everything if t["week"] == week
                    and source_of(t) == "lab"] for week in WEEKS}
    app_traces = [t for t in everything if source_of(t) == "app"]
    if app_traces:
        groups["app"] = app_traces
    groups["all"] = everything
    rows = {}
    details = {}
    for name, traces in groups.items():
        dims = report(traces)
        rows[name] = {d.name: d.value for d in dims}
        dates = sorted({t["started_at"][:10] for t in traces})
        details[name] = {
            "runs": len(traces),
            "weeks": sorted({t["week"] for t in traces}),
            "first_date_utc": dates[0] if dates else None,
            "last_date_utc": dates[-1] if dates else None,
            "evidence": {d.name: d.detail for d in dims},
        }
        cells = "".join(
            f"{'n/a':>16}" if d.value is None else f"{d.value:>16.2f}"
            for d in dims)
        print(f"{name:<7}{len(traces):>6}{cells}")

    print("\nEvidence gaps in the lab rows:")
    for week in WEEKS:
        for name, value in rows[week].items():
            if value is None:
                print(f"  week {week}, {name}: {details[week]['evidence'][name]}")
    elapsed = perf_counter() - start
    path = write_json("artifacts/week10_free.json", {
        "by_week": rows,
        "details": details,
        "trace_file": str(traces_path()[0]),
        "seconds": elapsed,
    })
    print(f"\nTrace loading and report: {elapsed:.4f}s. Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
