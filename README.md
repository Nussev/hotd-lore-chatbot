# HOTD Fandom Chatbot

A retrieval-augmented generation (RAG) chatbot that answers questions about House of the Dragon using real Reddit discourse as its knowledge base. User questions are embedded and matched against a FAISS vector index built from r/HouseOfTheDragon posts and comments. The top results are passed as context to Claude, which generates a grounded answer with source links back to the original threads.

## Tech Stack

| Component | Tool |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` via sentence-transformers |
| Vector search | FAISS (`IndexFlatL2`) |
| LLM | Claude (`claude-sonnet-4-6`) via Anthropic API |
| UI | Streamlit |
| Data format | JSONL (one record per line) |

## Project Structure

```
hotd-lore-chatbot/
├── data_raw/                          # Raw Reddit JSONL exports (gitignored)
│   ├── r_HouseOfTheDragon_posts.jsonl
│   └── r_HouseOfTheDragon_comments.jsonl
│
├── data_clean/
│   └── hotd_chunks.jsonl              # Filtered, chunked output (gitignored)
│
├── embeddings/
│   ├── hotd_embeddings.npy            # Embedding vectors, shape (N, 384)
│   ├── hotd_meta.jsonl                # Parallel metadata (chunk_id, title, score)
│   └── hotd.index                     # FAISS index file
│
├── scripts/
│   ├── process_reddit.py              # Filter posts + comments → hotd_chunks.jsonl
│   ├── chunk_strategy.py              # Defines how a post+comments become one chunk
│   ├── embed_chunks.py                # Embed chunks with sentence-transformers → .npy
│   ├── build_index.py                 # Load .npy → build and save FAISS index
│   ├── validate_chunks.py             # QA report on chunk quality and size
│   ├── test_parse.py                  # Peek at raw JSONL data
│   └── utils/
│       └── filters.py                 # Quality rules for posts and comments
│
├── rag/
│   ├── retriever.py                   # Load index + embed query → top-5 chunks
│   └── chat.py                        # Build prompt + call Claude → answer + sources
│
├── app/
│   └── streamlit_app.py               # Browser UI
│
├── .env                               # API key (gitignored)
├── .gitignore
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Anthropic API key in a `.env` file at the project root:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Running the Pipeline

Run these steps in order. Steps 1–3 only need to be run once (or whenever the source data changes).

```bash
# 1. Process raw Reddit data into chunks
python scripts/process_reddit.py

# 2. Embed chunks with sentence-transformers
python scripts/embed_chunks.py

# 3. Build the FAISS index from embeddings
python scripts/build_index.py

# 4. Launch the chat UI
streamlit run app/streamlit_app.py
```

Optional — validate chunk quality before embedding:

```bash
python scripts/validate_chunks.py --input data_clean/hotd_chunks.jsonl --output data_clean/validation_report.json
```
