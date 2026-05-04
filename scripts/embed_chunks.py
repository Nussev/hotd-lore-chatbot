import os
import sys
import json

import numpy as np
import orjson
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE    = os.path.join(ROOT, "data_clean", "hotd_chunks.jsonl")
OUTPUT_VECS   = os.path.join(ROOT, "embeddings", "hotd_embeddings.npy")
OUTPUT_META   = os.path.join(ROOT, "embeddings", "hotd_meta.jsonl")

# How many chunks to embed at once.
# Larger = faster, but uses more RAM.  64 is a safe default for most machines.
BATCH_SIZE = 64
MODEL_NAME = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# LOAD CHUNKS
# ---------------------------------------------------------------------------
def load_chunks(path):
    """Read every line of the JSONL file and return a list of chunk dicts."""
    chunks = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                chunks.append(orjson.loads(line))
            except Exception:
                print(f"  [WARN] Line {i} could not be parsed — skipping.")
    return chunks


# ---------------------------------------------------------------------------
# EMBED IN BATCHES
# ---------------------------------------------------------------------------
def embed_in_batches(model, texts, batch_size):
    """
    Split `texts` into groups of `batch_size`, embed each group,
    then stack everything into one big NumPy array.

    Why batching?
      Embedding one text at a time sends 18k separate jobs to the model.
      Batching groups them so the model can process many in parallel —
      roughly 10x faster on CPU, even faster on GPU.
    """
    all_vectors = []

    # range(0, total, batch_size) gives us the start index of each batch:
    # e.g. 0, 64, 128, 192, ... until we've covered all texts
    for start in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
        batch = texts[start : start + batch_size]

        # model.encode() returns a 2-D array of shape (batch_size, 384)
        # Each row is a 384-number "fingerprint" of that text
        vectors = model.encode(batch, show_progress_bar=False)
        all_vectors.append(vectors)

    # np.vstack stacks the list of 2-D arrays vertically into one big array
    # e.g. 282 batches of (64, 384) → one array of (18000, 384)
    return np.vstack(all_vectors)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    os.makedirs(os.path.join(ROOT, "embeddings"), exist_ok=True)

    # ---- Load data ----------------------------------------------------------
    print(f"Loading chunks from : {INPUT_FILE}")
    chunks = load_chunks(INPUT_FILE)
    print(f"Loaded {len(chunks)} chunks.\n")

    if not chunks:
        print("[ERROR] No chunks found. Run process_reddit.py first.")
        sys.exit(1)

    # ---- Extract texts ------------------------------------------------------
    # We only embed the primary text — that's what the AI will search over
    texts = [c.get("primary", {}).get("text", "") for c in chunks]

    # ---- Load model ---------------------------------------------------------
    print(f"Loading model       : {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.\n")

    # ---- Embed --------------------------------------------------------------
    print(f"Embedding {len(texts)} texts in batches of {BATCH_SIZE}...")
    embeddings = embed_in_batches(model, texts, BATCH_SIZE)

    # ---- Save vectors -------------------------------------------------------
    np.save(OUTPUT_VECS, embeddings)

    # ---- Save metadata ------------------------------------------------------
    # One line per chunk, same order as the rows in the .npy file.
    # Later, when FAISS returns row index i, we do meta[i] to get context.
    with open(OUTPUT_META, "w", encoding="utf-8") as f:
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            record = {
                "chunk_id":   chunk.get("chunk_id", ""),
                "post_id":    meta.get("post_id", ""),
                "post_title": meta.get("post_title", ""),
                "post_score": meta.get("post_score", 0),
                "subreddit":  meta.get("subreddit", ""),
            }
            f.write(json.dumps(record) + "\n")

    # ---- Summary ------------------------------------------------------------
    vec_size_mb  = os.path.getsize(OUTPUT_VECS)  / 1_000_000
    meta_size_kb = os.path.getsize(OUTPUT_META) / 1_000

    print("\n" + "=" * 50)
    print("  EMBEDDING COMPLETE")
    print("=" * 50)
    print(f"  Chunks embedded    : {len(chunks)}")
    print(f"  Array shape        : {embeddings.shape}  (chunks × dimensions)")
    print(f"  Vectors saved to   : {OUTPUT_VECS}  ({vec_size_mb:.1f} MB)")
    print(f"  Metadata saved to  : {OUTPUT_META}  ({meta_size_kb:.1f} KB)")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
