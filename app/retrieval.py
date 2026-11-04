"""The index and the two retrievers. TODO 3.

Chroma is a black box here, exactly as the syllabus asks. You put vectors in
with metadata and you get ranked ids out. What is worth your attention is
what you put in and how you score what comes back.

Two retrievers, because block 2 compares them:

  dense     embeddings, cosine similarity. Good at meaning, indifferent to
            exact strings.
  keyword   term overlap. The reverse. Deliberately crude, so it is obvious
            what it is doing.
"""

from __future__ import annotations

import json
import re
import urllib.request

from .chunking import Chunk

from project.models import EMBED, OLLAMA_URL

EMBED_MODEL = EMBED.name


def embed(texts: list[str], batch: int = 32) -> list[list[float]]:
    """TODO 3a. Embed a list of texts, in batches.

    One call per chunk is the obvious version and it is roughly thirty times
    slower on this corpus. The endpoint takes a list, so give it one.

    POST to f"{OLLAMA_URL}/api/embed" with a JSON body of
    {"model": EMBED_MODEL, "input": [...]} and read the "embeddings" key.
    """
    vectors: list[list[float]] = []

    for start in range(0, len(texts), batch):
        body = json.dumps({
            "model": EMBED_MODEL,
            "input": texts[start:start + batch],
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{OLLAMA_URL}/api/embed", data=body,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=180) as response:
            vectors.extend(json.loads(response.read())["embeddings"])

    return vectors


class DenseIndex:
    """TODO 3b. Build once per configuration, then query it."""

    def __init__(self, chunks: list[Chunk], name: str = "run_a"):
        """Build the index.

        chromadb.EphemeralClient(), then get_or_create_collection(name),
        then add() with ids, embeddings, and metadatas carrying doc_id and
        section.

        Give the collection a NAME that encodes the configuration. Two
        chunkings have to be able to coexist during the block 3 sweep, and
        rebuilding without deleting is the classic way to end up with two
        chunkings in one index and numbers nobody can explain.

        Keep a dict from chunk_id to Chunk, because search has to map the
        ids Chroma returns back to objects. Set self.dim so the brief's
        conditions line has something to record.
        """
        import chromadb

        self.by_id = {chunk.chunk_id: chunk for chunk in chunks}
        vectors = embed([chunk.text for chunk in chunks])
        self.dim = len(vectors[0]) if vectors else 0

        client = chromadb.EphemeralClient()
        # Ephemeral clients share state inside one process, so delete any
        # collection left by an earlier build under the same name rather
        # than adding a second chunking on top of it.
        try:
            client.delete_collection(name)
        except Exception:
            pass
        self.collection = client.get_or_create_collection(
            name, metadata={"hnsw:space": "cosine"})

        if chunks:
            self.collection.add(
                ids=[chunk.chunk_id for chunk in chunks],
                embeddings=vectors,
                documents=[chunk.text for chunk in chunks],
                metadatas=[{"doc_id": chunk.doc_id, "section": chunk.section}
                           for chunk in chunks],
            )

    def search(self, query: str, k: int = 20) -> list[Chunk]:
        """Embed the query, ask the collection, map ids back to Chunks."""
        k = min(k, len(self.by_id))
        if k <= 0:
            return []

        [query_vector] = embed([query])
        result = self.collection.query(query_embeddings=[query_vector],
                                       n_results=k, include=["distances"])
        return [self.by_id[chunk_id] for chunk_id in result["ids"][0]]


def keyword_search(chunks: list[Chunk], query: str,
                   k: int = 20) -> list[Chunk]:
    """TODO 3c. Term overlap. No model, no cost.

    Score each chunk by how many query terms appear in it, return the top k.
    Crude on purpose: in block 2 you will see a document that repeats a term
    in the wrong section outrank the section that answers the question.

    Break ties deterministically, by chunk_id, or two runs of your own code
    will disagree and you will spend ten minutes blaming the embedder.
    """
    def terms(text: str) -> set[str]:
        # [\w-]+ keeps "RB-1140b" as one token, which is the whole point of
        # the rare-token question. Words of two letters or fewer are dropped.
        return {t.casefold() for t in re.findall(r"[\w-]+", text) if len(t) > 2}

    query_terms = terms(query)
    if k <= 0 or not query_terms:
        return []

    scored = []
    for chunk in chunks:
        hits = len(query_terms & terms(chunk.text))
        if hits:
            scored.append((hits, chunk))

    # Most hits first, ties broken by chunk_id so every run agrees.
    scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
    return [chunk for _, chunk in scored[:k]]
