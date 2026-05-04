"""
chat.py — takes a user question and retrieved chunks from retriever.py,
builds a prompt, calls Claude, and returns the answer + source links.
"""

import anthropic

# ---------------------------------------------------------------------------
# CLIENT + CONSTANTS
# ---------------------------------------------------------------------------

# The client reads ANTHROPIC_API_KEY from your environment automatically.
# Get a key at: https://console.anthropic.com/
client = anthropic.Anthropic()

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------
# The system prompt defines Claude's "personality" for this chatbot.
# It tells Claude to ONLY use the provided Reddit sources — this is what
# makes it a RAG chatbot rather than just a general-purpose assistant.

SYSTEM_PROMPT = (
    "You are a House of the Dragon fandom expert. "
    "Answer questions based only on the Reddit discussions provided to you — "
    "do not use outside knowledge. "
    "Be direct and specific. "
    "Cite sources by referring to their post titles naturally in your answer "
    "(for example: \"As discussed in 'Post Title Here'...\"). "
    "If the provided sources do not contain enough information to answer "
    "the question, say so honestly rather than guessing."
)


# ---------------------------------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------------------------------

def _build_user_message(query: str, chunks: list) -> str:
    """
    Format the retrieved chunks and user question into one message string.

    Each chunk becomes a clearly labeled block so Claude knows where
    each piece of information comes from and can cite it by title.

    Example output:
        [Source 1: "Daemon Targaryen and Caraxes"]
        Daemon Targaryen is the rider of Caraxes...

        ---

        [Source 2: "Episode 4 Discussion"]
        ...

        ---

        Based on the Reddit discussions above, please answer this question:
        Who rides Caraxes?
    """
    sections = []

    for i, chunk in enumerate(chunks, 1):
        title = chunk.get("post_title", "Untitled")
        text = chunk.get("text", "")
        # Label each block with its number and post title
        sections.append(f'[Source {i}: "{title}"]\n{text}')

    # Join blocks with a divider so Claude can clearly see where each ends
    sources_block = "\n\n---\n\n".join(sections)

    return (
        f"{sources_block}\n\n"
        f"---\n\n"
        f"Based on the Reddit discussions above, please answer this question:\n"
        f"{query}"
    )


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def get_answer(query: str, retrieved_chunks: list) -> dict:
    """
    Call Claude with the question + retrieved context, return answer + sources.

    Parameters:
        query            — the user's question (plain string)
        retrieved_chunks — list of dicts from retriever.retrieve(), each with:
                             chunk_id, post_id, post_title, post_score,
                             subreddit, distance, text

    Returns a dict with:
        "answer"  — Claude's response as a string
        "sources" — list of dicts, each with "post_title" and "url"
                    (a Reddit link constructed from the post_id)
    """

    # Step 1: Format the chunks + question into one big user message
    user_message = _build_user_message(query, retrieved_chunks)

    # Step 2: Call the Anthropic API
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    # Step 3: Pull the answer text out of the response
    # response.content is a list of content blocks (TextBlock, etc.)
    # We grab the first block whose type is "text"
    answer = next(
        (block.text for block in response.content if block.type == "text"),
        "No answer generated.",
    )

    # Step 4: Build the source list — one entry per retrieved chunk
    # Reddit URLs follow the pattern:
    #   https://reddit.com/r/<subreddit>/comments/<post_id>
    sources = [
        {
            "post_title": chunk.get("post_title", "Untitled"),
            "url": (
                f"https://reddit.com/r/HouseOfTheDragon/comments/"
                f"{chunk.get('post_id', '')}"
            ),
        }
        for chunk in retrieved_chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
    }
