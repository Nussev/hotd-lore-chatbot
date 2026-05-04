import os
import sys

import numpy as np
import faiss

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_VECS   = os.path.join(ROOT, "embeddings", "hotd_embeddings.npy")
OUTPUT_INDEX = os.path.join(ROOT, "embeddings", "hotd.index")


def main():
    # ---- Load vectors -------------------------------------------------------
    if not os.path.exists(INPUT_VECS):
        print(f"[ERROR] Embeddings file not found: {INPUT_VECS}")
        print("        Run embed_chunks.py first.")
        sys.exit(1)

    print(f"Loading embeddings from : {INPUT_VECS}")
    embeddings = np.load(INPUT_VECS)
    print(f"Loaded array shape      : {embeddings.shape}  (chunks × dimensions)\n")

    # ---- Prepare for FAISS --------------------------------------------------
    # FAISS requires float32. np.load gives float64 by default, so we cast.
    # Skipping this step causes a silent wrong-result bug or a hard crash.
    embeddings = embeddings.astype(np.float32)

    # Number of dimensions per vector (384 for all-MiniLM-L6-v2)
    dimension = embeddings.shape[1]

    # ---- Build index --------------------------------------------------------
    # IndexFlatL2 = exact nearest-neighbor search using Euclidean (L2) distance.
    # On normalized vectors (which sentence-transformers produces) this is
    # equivalent to cosine similarity, so results are correct either way.
    # "Flat" means no compression or approximation — fine up to ~1M vectors.
    print(f"Building IndexFlatL2 (dimension={dimension})...")
    index = faiss.IndexFlatL2(dimension)

    # add() ingests all vectors into the index in one call
    index.add(embeddings)
    print(f"Vectors in index        : {index.ntotal}")

    # ---- Save ---------------------------------------------------------------
    faiss.write_index(index, OUTPUT_INDEX)

    index_size_kb = os.path.getsize(OUTPUT_INDEX) / 1_000

    print("\n" + "=" * 50)
    print("  INDEX BUILD COMPLETE")
    print("=" * 50)
    print(f"  Vectors indexed    : {index.ntotal}")
    print(f"  Dimensions         : {dimension}")
    print(f"  Index saved to     : {OUTPUT_INDEX}  ({index_size_kb:.1f} KB)")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
