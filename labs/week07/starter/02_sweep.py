"""Homework and stretch. The chunk sweep, and Q05 asked as two questions.

    python 02_sweep.py

Reports questions by name, never a mean, because the average barely moves.
Writes artifacts/week07_sweep.json.
"""

from __future__ import annotations

import time

from chunking import load_chunks
from goldset import GOLD
from metrics import gold_keys, score
from retrieval import DenseIndex, keyword_search

from project.trace import write_json

CONFIGS = [(300, 40), (600, 80), (1200, 120)]
K = 5

Q05_PARTS = [
    "Within how many days of moving to Remerbaach must I declare my arrival "
    "at the commune?",
    "I own a car. How do I apply for a resident parking vignette?",
]


def section_ranks(ranked, question) -> dict[str, int | None]:
    """Rank of the first chunk of EACH gold section, for multi-section gold."""
    out: dict[str, int | None] = {}
    for key in sorted(gold_keys(question)):
        out["::".join(key)] = next(
            (r for r, c in enumerate(ranked, start=1) if c.key == key), None)
    return out


def merge_round_robin(result_lists, k: int):
    """Take the best of each list in turn, skipping chunks already taken."""
    merged, seen = [], set()
    for position in range(max(len(r) for r in result_lists)):
        for results in result_lists:
            if position < len(results):
                chunk = results[position]
                if chunk.chunk_id not in seen:
                    seen.add(chunk.chunk_id)
                    merged.append(chunk)
    return merged[:k]


def main() -> int:
    q05 = next(q for q in GOLD if q.qid == "Q05")
    report = []

    for size, overlap in CONFIGS:
        chunks = load_chunks(size=size, overlap=overlap)
        started = time.perf_counter()
        index = DenseIndex(chunks, name=f"sweep_s{size}_o{overlap}")
        elapsed = time.perf_counter() - started

        rows = {}
        for question in GOLD:
            if not question.answerable:
                continue
            dense = index.search(question.question, k=len(chunks))
            keyword = keyword_search(chunks, question.question, k=len(chunks))
            d, kw = score(dense, question, K), score(keyword, question, K)
            rows[question.qid] = {
                "dense_rank": d.rank, "keyword_rank": kw.rank,
                "dense_recall": d.recall_at_k,
                "keyword_recall": kw.recall_at_k,
            }

        ranked = index.search(q05.question, k=len(chunks))
        whole = section_ranks(ranked, q05)

        part_results = [index.search(part, k=K) for part in Q05_PARTS]
        merged = merge_round_robin(part_results, K)
        split = {
            "part_ranks": [
                section_ranks(index.search(part, k=len(chunks)), q05)
                for part in Q05_PARTS],
            "merged_top5": [c.chunk_id for c in merged],
            "merged_recall": score(merged, q05, K).recall_at_k,
        }

        report.append({
            "size": size, "overlap": overlap, "chunks": len(chunks),
            "dim": index.dim, "index_seconds": round(elapsed, 2),
            "rows": rows, "q05_section_ranks": whole, "q05_split": split,
        })

        print(f"\n{size}/{overlap}: {len(chunks)} chunks, "
              f"indexed in {elapsed:.1f}s")
        print(f"  Q05 as asked, per section: {whole}")
        print(f"  Q05 split and merged: recall@{K} "
              f"{split['merged_recall']:.2f}  {split['merged_top5']}")

    print(f"\n{'qid':<5}" + "".join(f"{f'{s} d/kw':>12}" for s, _ in CONFIGS)
          + "  recall@5 d/kw per size")
    for question in GOLD:
        if not question.answerable:
            continue
        cells, recalls = "", []
        for config in report:
            row = config["rows"][question.qid]
            cells += f"{str(row['dense_rank']) + '/' + str(row['keyword_rank']):>12}"
            recalls.append(f"{row['dense_recall']:.2f}/{row['keyword_recall']:.2f}")
        print(f"{question.qid:<5}{cells}  {'  '.join(recalls)}")

    write_json("artifacts/week07_sweep.json", {"k": K, "configs": report})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
