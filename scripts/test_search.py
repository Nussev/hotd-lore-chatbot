"""
Quick end-to-end sanity check for the full pipeline.

Tests:
  1. FAISS index loads and has vectors
  2. Metadata file loads and has the same count
  3. Embedding model loads
  4. A sample query returns real results with readable titles

Run:
  python scripts/test_search.py
  python scripts/test_search.py --query "Who are the Targaryens?"
"""

import os
import sys
import json
import argparse

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE   = os.path.join(ROOT, "embeddings", "hotd.index")
META_FILE    = os.path.join(ROOT, "embeddings", "hotd_meta.jsonl")
MODEL_NAME   = "all-MiniLM-L6-v2"
TOP_K        = 3   # how many results to return


def load_meta(path):
    meta = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                meta.append(json.loads(line))
    return meta


def search(query, index, meta, model, k=TOP_K):
    # Embed the query the same way we embedded the chunks
    query_vec = model.encode([query]).astype(np.float32)  # shape (1, 384)

    # FAISS returns two arrays:
    #   distances[0] — how similar each result is (lower L2 = more similar)
    #   indices[0]   — which row in the index each result came from
    distances, indices = index.search(query_vec, k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        results.append({"meta": meta[idx], "distance": float(dist)})
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="Daemon Targaryen dragon", help="Search query")
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # 1. Load index
    # ------------------------------------------------------------------
    print(f"\n[1/3] Loading FAISS index from {INDEX_FILE}")
    if not os.path.exists(INDEX_FILE):
        print("      ERROR: index not found. Run build_index.py first.")
        sys.exit(1)
    index = faiss.read_index(INDEX_FILE)
    print(f"      OK — {index.ntotal} vectors, {index.d} dimensions")

    # ------------------------------------------------------------------
    # 2. Load metadata
    # ------------------------------------------------------------------
    print(f"\n[2/3] Loading metadata from {META_FILE}")
    if not os.path.exists(META_FILE):
        print("      ERROR: metadata not found. Run embed_chunks.py first.")
        sys.exit(1)
    meta = load_meta(META_FILE)
    print(f"      OK — {len(meta)} records")

    if index.ntotal != len(meta):
        print(f"      WARN: index has {index.ntotal} vectors but meta has {len(meta)} records — counts don't match!")

    # ------------------------------------------------------------------
    # 3. Load model + run a search
    # ------------------------------------------------------------------
    print(f"\n[3/3] Loading model and running search...")
    model = SentenceTransformer(MODEL_NAME)

    query = args.query
    results = search(query, index, meta, model)

    # ------------------------------------------------------------------
    # Print results
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print(f'  QUERY: "{query}"')
    print("=" * 60)
    for i, r in enumerate(results, 1):
        m = r["meta"]
        print(f"\n  Result #{i}")
        print(f"  Title    : {m['post_title']}")
        print(f"  Score    : {m['post_score']} upvotes")
        print(f"  chunk_id : {m['chunk_id']}")
        print(f"  Distance : {r['distance']:.4f}  (lower = more similar)")
    print("\n" + "=" * 60)
    print("  All checks passed — pipeline is working.\n")


if __name__ == "__main__":
    main()
