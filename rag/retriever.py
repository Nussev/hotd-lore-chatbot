"""
retriever.py — loads the FAISS index and chunk data once at startup,
then exposes a single function: retrieve(query) → list of top results.
"""

import json

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from core.config import EMBEDDING_MODEL, TOP_K, OFF_TOPIC_THRESHOLD
from core.config import INDEX_FILE, META_FILE, CHUNKS_FILE

# ---------------------------------------------------------------------------
# LOAD EVERYTHING ONCE AT MODULE LEVEL
#
# Python runs this code the first time the module is imported.
# Every subsequent import reuses the same already-loaded objects —
# so the model and index are only loaded once per program run,
# not once per query call.
# ---------------------------------------------------------------------------
print("[retriever] Loading FAISS index...")
_index = faiss.read_index(str(INDEX_FILE))

print("[retriever] Loading metadata...")
_meta = []
with open(META_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            _meta.append(json.loads(line))

print("[retriever] Loading chunk text lookup...")
# Build a dict of { chunk_id → primary.text } so we can quickly fetch
# the full post text by chunk_id after FAISS returns an index position.
_chunk_text: dict[str, str] = {}
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            chunk = json.loads(line)
            cid = chunk.get("chunk_id", "")
            text = chunk.get("primary", {}).get("text", "")
            if cid:
                _chunk_text[cid] = text
        except json.JSONDecodeError:
            continue

print(f"[retriever] Loading embedding model: {EMBEDDING_MODEL}")
_model = SentenceTransformer(EMBEDDING_MODEL)

print(f"[retriever] Ready — {_index.ntotal} chunks indexed.\n")


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------
def retrieve(query: str) -> list[dict]:
    """
    Embed `query` and return the top-5 most relevant chunks.

    Each result dict contains:
      chunk_id    — unique ID for the chunk
      post_id     — Reddit post ID
      post_title  — title of the Reddit post
      post_score  — upvote count
      subreddit   — should always be HouseOfTheDragon
      distance    — L2 distance from the query (lower = more similar)
      text        — the full primary.text the AI will use to answer

    Example:
      results = retrieve("Who rides Caraxes?")
      print(results[0]["post_title"])
    """

    # Step 1: Embed the query using the same model that was used to embed chunks.
    # model.encode() returns a 2-D array of shape (1, 384).
    query_vec = _model.encode([query])

    # Step 2: FAISS requires float32. sentence-transformers returns float32
    # by default, but we cast explicitly to be safe.
    query_vec = query_vec.astype(np.float32)  # shape: (1, 384)

    # Step 3: Search the index.
    # index.search(vector, k) returns two arrays, both shape (1, k):
    #   distances — L2 distance for each result (lower = closer = more relevant)
    #   indices   — which row in the index each result came from
    distances, indices = _index.search(query_vec, TOP_K)

    # Step 4: Build result list using the flat arrays distances[0] / indices[0].
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        # idx is the row number in the FAISS index.
        # Because we added vectors in the same order as the metadata file,
        # _meta[idx] gives us the metadata for that chunk.
        meta = _meta[idx]
        chunk_id = meta["chunk_id"]

        # Look up the full text using the chunk_id we stored at load time.
        text = _chunk_text.get(chunk_id, "")

        results.append({
            "chunk_id":   chunk_id,
            "post_id":    meta["post_id"],
            "post_title": meta["post_title"],
            "post_score": meta["post_score"],
            "subreddit":  meta["subreddit"],
            "distance":   round(float(dist), 4),
            "text":       text,
        })

    return results


def is_off_topic(chunks: list[dict]) -> bool:
    """Return True if the best retrieved chunk is too distant from the query."""
    if not chunks:
        return True
    return chunks[0]["distance"] > OFF_TOPIC_THRESHOLD
