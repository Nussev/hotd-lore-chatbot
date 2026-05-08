# HOTD Fandom Chatbot — Dev Notes

Engineering decisions and implementation highlights for this project.

---

## What Was Built

A full-stack AI chatbot that answers questions about House of the Dragon using real Reddit discourse as its knowledge base. The app retrieves the most relevant Reddit posts and comments for any question, then passes them as context to Claude to generate a grounded, cited answer.

---

## Key Engineering Implementations

### RAG Pipeline (Retrieval-Augmented Generation)
Designed and built an end-to-end data pipeline that transforms raw Reddit JSONL exports into a searchable vector database. The pipeline filters 115,000+ posts and 3.5M+ comments down to high-quality chunks using configurable quality rules (minimum score, comment count, body length), embeds each chunk using `sentence-transformers` (`all-MiniLM-L6-v2`), and stores the resulting vectors in a FAISS flat L2 index for fast similarity search.

### Vector Similarity Search with FAISS
Implemented semantic search using Facebook AI Similarity Search (FAISS). User questions are embedded with the same model used to build the index, then the nearest neighbors are retrieved in milliseconds regardless of index size. This means the chatbot finds conceptually related posts — not just keyword matches.

### Anthropic Claude Integration with Prompt Caching
Integrated Claude (`claude-sonnet-4-6`) via the Anthropic API to generate answers from retrieved context. Implemented **prompt caching** using Anthropic's `cache_control` API, which stores the system prompt server-side. Cache hits are charged at ~10% of the normal input token cost, meaningfully reducing API spend on every conversation after the first message.

### Multi-Turn Conversation Memory
Extended the chatbot from stateless Q&A to a real conversational system. Prior turns are passed to Claude as a structured message history, enabling follow-up questions like "what about her sister?" or "why did you say that?" — without re-injecting source chunks for old turns, keeping context size compact.

### Streamlit Chat UI
Built a browser-based chat interface with session-scoped conversation history, expandable source citations linking back to original Reddit threads, and a `@st.cache_resource` pattern to load the FAISS index and embedding model only once per session.

---

## Tech Stack

| Layer | Tool |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` via sentence-transformers |
| Vector search | FAISS (`IndexFlatL2`) |
| LLM | Claude `claude-sonnet-4-6` via Anthropic API |
| UI | Streamlit |
| Data format | JSONL |
| Runtime | Python 3.12, virtualenv |

---

## Data

- **Source**: r/HouseOfTheDragon Reddit exports (posts + comments)
- **Raw size**: ~115k posts, ~3.5M comments
- **After filtering**: ~3,500 high-quality post chunks
- **Chunk format**: post title + body + top-scored comments concatenated into one text block per post
