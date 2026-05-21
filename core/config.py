from pathlib import Path

# Project root — two levels up from here (core/config.py → core/ → project root)
ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# File paths
# ---------------------------------------------------------------------------
INDEX_FILE   = ROOT / "embeddings" / "hotd.index"       # FAISS binary index
META_FILE    = ROOT / "embeddings" / "hotd_meta.jsonl"  # parallel chunk metadata
CHUNKS_FILE  = ROOT / "data_clean" / "hotd_chunks.jsonl"  # full chunk text lookup
FEEDBACK_LOG = ROOT / "logs" / "feedback.jsonl"         # user thumbs-up/down log

# ---------------------------------------------------------------------------
# Embedding model
# WARNING: must match the model used in scripts/embed_chunks.py.
# Changing this requires re-running embed_chunks.py and build_index.py.
# ---------------------------------------------------------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------
TOP_K = 5  # number of chunks returned per query

# Squared L2 distance above which a query is considered off-topic.
# all-MiniLM-L6-v2 produces unit vectors, so: squared_L2 = 2*(1 - cosine_sim)
# 1.5 ≈ cosine similarity of 0.25 — essentially no thematic overlap with the index.
# Tune down if real HOTD questions get blocked; tune up if off-topic slips through.
OFF_TOPIC_THRESHOLD = 1.5

# ---------------------------------------------------------------------------
# Claude
# ---------------------------------------------------------------------------
CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_TOKENS   = 1024  # max tokens in Claude's response

# ---------------------------------------------------------------------------
# UI strings
# ---------------------------------------------------------------------------
OFF_TOPIC_REPLY = (
    "OPE! This chatbot is built specifically for **House of the Dragon** fandom discussion "
    "— it only knows what r/HouseOfTheDragon has talked about. I can't help with that one.\n\n"
    "Try asking something like:\n"
    "- *What does the fandom think of Daemon?*\n"
    "- *Who rides Caraxes?*\n"
    "- *How did people react to the season 2 finale?*"
)

