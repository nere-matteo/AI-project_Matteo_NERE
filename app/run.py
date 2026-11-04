"""Search the memory store from the command line.

    python -m app.run --subject "A. Muller" "How do I register a new address?"

A thin entry point for the week 7 wire-in. It calls MemoryStore.search and
prints what came back. There is no agent or model call here.
"""

from __future__ import annotations

import argparse

from .memory import MemoryStore


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("query")
    args = ap.parse_args()

    hits = MemoryStore.load().search(args.subject, args.query, args.k)
    for n, text in enumerate(hits, start=1):
        print(f"[{n}] {text}\n")
    print(f"memory.search subject={args.subject!r} k={args.k} hits={len(hits)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
