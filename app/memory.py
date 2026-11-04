"""The memory store, and the handle. TODO 1 to 3.

Two things live here and they are easy to confuse.

**Memory** is what the agent remembers about a resident across runs: facts,
written once and searched later. It is a store.

**A handle** is a name for a piece of state that the agent carries in its own
messages. It is not memory, it is an address. `open_case` mints one, and
every later call passes it back as an ordinary argument.

The distinction is the whole week. Block 2 shows why: when the protocol stops
carrying state for you, the state does not vanish, it becomes an argument
with a name the model can see.
"""

from __future__ import annotations

import json
import math
import secrets
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .chunking import load_chunks
from .retrieval import DenseIndex, embed

DEFAULT_PATH = Path("artifacts/memory_store.json")

# The configuration DECISIONS.md chose in week 7.
CHUNK_SIZE = 600
CHUNK_OVERLAP = 80


@lru_cache(maxsize=1)
def _corpus_index() -> DenseIndex:
    """Build the corpus index once per process, on the first search."""
    chunks = load_chunks(size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    return DenseIndex(chunks, name=f"corpus_s{CHUNK_SIZE}_o{CHUNK_OVERLAP}")


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return 1.0 - dot / norm if norm else 1.0


@dataclass
class Fact:
    subject: str
    kind: str
    text: str
    handle: str
    written_at: str


@dataclass
class MemoryStore:
    """A file-backed store of facts, searched together with the corpus.

    Facts stay in the JSON file. Only `search` knows about embeddings and the
    vector store, so the week 7 retriever changed one method body.
    """

    path: Path = DEFAULT_PATH
    facts: list[Fact] = field(default_factory=list)
    cases: dict[str, str] = field(default_factory=dict)

    # ----------------------------------------------------------------
    # TODO 1. Writing, and the handle it returns.
    # ----------------------------------------------------------------

    def write(self, subject: str, kind: str, text: str) -> str:
        """TODO 1. Append one fact and return a handle for it.

        Three decisions here, and all three go in DECISIONS.md with a reason.

        What does a handle look like? A sequential `fact-0007` tells anyone
        who sees it how many facts exist and lets them guess `fact-0006`,
        which is a read of somebody else's data. Week 12 attacks exactly
        this.

        What happens when a new fact contradicts an older one? Keeping both
        means `recall` can return two contradictory facts and something has
        to cope. Overwriting means losing what changed and when. Pick one.

        How long does a record live? Nothing here expires, which is a choice
        and the wrong one for a real service holding residents' data. If you
        keep it, say so rather than leaving it unsaid.
        """
        handle = f"fact-{secrets.token_hex(16)}"

        self.facts.append(Fact(
            subject=subject,
            kind=kind,
            text=text,
            handle=handle, 
            written_at=time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            ),
        ))

        self.save()
        return handle

    # ----------------------------------------------------------------
    # TODO 2. Searching, and what k costs.
    # ----------------------------------------------------------------

    def search(self, subject: str, query: str, k: int = 3) -> list[str]:
        """Return the k passages closest to the query, by dense retrieval.

        Candidates are this subject's facts plus the public corpus. Facts are
        scoped to the subject BEFORE scoring, so one resident's memory cannot
        leak into another's conversation. The corpus holds no resident data,
        so every subject searches all of it. Both are scored by cosine
        distance, so they rank on one scale.

        Facts are embedded on every call. That is fine at this size, but a
        subject with hundreds of facts would need their vectors stored.
        """
        if k <= 0 or not query.strip():
            return []

        # Newest first, so that the stable sort below favours newer facts on
        # a tie, as week 6 decided.
        own = [fact for fact in reversed(self.facts)
               if fact.subject == subject]
        query_vector, *fact_vectors = embed(
            [query, *(f"{fact.kind} {fact.text}" for fact in own)])

        scored = [(_cosine_distance(query_vector, vector), fact.text)
                  for fact, vector in zip(own, fact_vectors)]

        index = _corpus_index()
        result = index.collection.query(
            query_embeddings=[query_vector],
            n_results=min(k, len(index.by_id)), include=["distances"])
        scored += [(distance, index.by_id[chunk_id].text)
                   for chunk_id, distance
                   in zip(result["ids"][0], result["distances"][0])]

        scored.sort(key=lambda item: item[0])
        return [text for _, text in scored[:k]]

    # ----------------------------------------------------------------
    # TODO 3. Forgetting, which is not optional.
    # ----------------------------------------------------------------

    def forget(self, handle: str) -> bool:
        """TODO 3. Hard delete by handle. Return whether it existed.

        Not optional. A store that can only be written to is not a store you
        can operate, and "we keep everything forever" is an answer with a
        legal department attached to it.

        One line in DECISIONS.md about what this does NOT reach: anything
        already copied into a running conversation's messages. Deleting the
        fact does not un-say it.
        """
        remaining = [
            fact for fact in self.facts
            if fact.handle != handle
        ] 

        if len(remaining) == len(self.facts):
            return False 

        self.facts = remaining
        self.save()
        return True

    # ----------------------------------------------------------------
    # The handle, which is block 2's subject
    # ----------------------------------------------------------------

    def open_case(self, subject: str) -> str:
        """Mint an explicit handle for a piece of ongoing state."""
        handle = f"case-{secrets.token_hex(6)}"
        self.cases[handle] = subject
        self.save()
        return handle

    def subject_of(self, handle: str) -> str | None:
        return self.cases.get(handle)

    # ----------------------------------------------------------------
    # Persistence
    # ----------------------------------------------------------------

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({
            "facts": [vars(f) for f in self.facts],
            "cases": self.cases,
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = DEFAULT_PATH) -> "MemoryStore":
        store = cls(path=path)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            store.facts = [Fact(**f) for f in data.get("facts", [])]
            store.cases = data.get("cases", {})
        return store
