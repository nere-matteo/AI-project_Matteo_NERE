"""Block 4, completed. TODO 8. One variant per group.

    python 02_stretch.py --variant model --replay
    python 02_stretch.py --variant voting --replay

The written answers are at the bottom.
"""

from __future__ import annotations

import argparse
import collections
import time

from queries import QUERIES
from router import CONFIDENCE_FLOOR, SAFE_DEFAULT, apply_policy, classify
from scoring import report, score_routes

from project.models import LARGE, SMALL
from project.fixtures import ReplayClient
from project.trace import utc_now, write_json

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "compare_mod", Path(__file__).with_name("01_compare.py"))
_cmp = importlib.util.module_from_spec(_spec)
sys.modules["compare_mod"] = _cmp
_spec.loader.exec_module(_cmp)


# --------------------------------------------------------------------------
# TODO 8. One variant. Your instructor assigns you one.
# --------------------------------------------------------------------------

def variant_model(client, prediction: str | None = None) -> None:
    """Variant A. Same prompt, same queries, same policy. Only the model.

    Run the classifier over the twenty four queries on SMALL and on LARGE,
    score both, and report per route as counts.

    Report four things per model, not one:
      * route accuracy, and route accuracy excluding the ambiguous four
      * how often the evidence span came back verbatim
      * the minimum and maximum confidence, and how many distinct values
      * the resident memory, which is in project/models.py

    Predict which model wins before you run it, and write the prediction
    down. Then read the confidence range carefully. One of the two models
    tells you something about your threshold from TODO 3a that you cannot
    unsee.
    """
    comparison = {
        "variant": "model",
        "prediction": prediction,
        "run_date": utc_now(),
        "source": "recording" if isinstance(client, ReplayClient) else "live",
        "temperature": 0.0,
        "confidence_floor": CONFIDENCE_FLOOR,
        "safe_default": SAFE_DEFAULT,
        "scored_against": "applied_route",
        "models": [],
    }

    for model in (SMALL, LARGE):
        print(f"\nClassifying {len(QUERIES)} queries with {model.name}...", flush=True)
        results, metas, cases = [], [], []

        for query in QUERIES:
            decision, meta = classify(
                client, query.text, model=model.name, temperature=0.0)
            routed = apply_policy(decision, query.text)
            results.append(routed)
            metas.append(meta)
            cases.append({
                "case_id": query.id,
                "gold_route": query.route,
                "ambiguous": query.ambiguous,
                "decision": decision.model_dump() if decision else None,
                "applied_route": routed.applied_route,
                "policy_fired": routed.policy_fired,
                "evidence_ok": routed.evidence_ok,
                **meta,
            })
            print(f"  {query.id}: {routed.applied_route}", flush=True)

        board = score_routes(results, QUERIES)
        tokens, seconds = _cmp.totals(metas)
        confidence = {
            "min": min(board.confidences) if board.confidences else None,
            "max": max(board.confidences) if board.confidences else None,
            "distinct": len(set(board.confidences)),
        }
        print(report(board, model.name))
        print(f"  exact confidence range: {confidence['min']} to {confidence['max']}")
        print(f"  resident memory (course reference): {model.resident_gb} GB")
        print(f"  classification cost: {tokens} tokens, {seconds:.1f} seconds")

        comparison["models"].append({
            "model": model.name,
            "hits": board.hits,
            "total": board.total,
            "unambiguous": [board.unambiguous_hits, board.unambiguous_total],
            "per_route": board.per_route,
            "confusion": {
                f"{gold}->{applied}": n
                for (gold, applied), n in board.confusion.items()
            },
            "policy_fired": dict(board.policy_fired),
            "evidence_ok": board.evidence_ok,
            "confidence": confidence,
            "resident_gb": model.resident_gb,
            "memory_source": "course reference from project/models.py",
            "tokens": tokens,
            "seconds": seconds,
            "cases": cases,
        })
        write_json("artifacts/week03_model_comparison.json", comparison)

    small, large = comparison["models"]
    if small["hits"] == large["hits"]:
        print(f"\nBoth models scored {small['hits']}/{small['total']}.")
    else:
        winner = max(comparison["models"], key=lambda result: result["hits"])
        print(f"\nMore correct applied routes on this set: {winner['model']} "
              f"({winner['hits']}/{winner['total']}).")


def variant_voting(client, k: int = 3) -> None:
    """Variant B. Classify k times at temperature 0.7, majority wins.

    Run sequentially rather than in threads. Your endpoint answers one
    request at a time, so a thread pool buys you nothing here, and finding
    that out is worth more than the speedup you expected.

    Score the majority result, but the number to report is not the accuracy.
    It is the set of queries where the k votes disagreed. Print it, and put
    it next to the list of ambiguous query ids.

    Then ask what that set is worth. Voting costs k times as much for a step
    that was already the cheap one, so as a way to decide it is a poor buy.
    As a way to detect something, it may be a very good one.
    """
    raise NotImplementedError("TODO 8: variant B, voting")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=("model", "voting"), required=True)
    ap.add_argument("--replay", action="store_true")
    ap.add_argument("--prediction", choices=("small", "large", "tie"),
                    help="Prediction made before running the model comparison")
    args = ap.parse_args()

    client = _cmp.get_client(args.replay)
    if args.variant == "model":
        variant_model(client, prediction=args.prediction)
    else:
        variant_voting(client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
