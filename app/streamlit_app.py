import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from rag.retriever import retrieve, is_off_topic
from rag.chat import get_answer

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="HOTD Fandom Chat",
    page_icon="🐉",
    layout="centered",
)

# ---------------------------------------------------------------------------
# FEEDBACK LOGGING
# ---------------------------------------------------------------------------
_LOG_FILE = Path(__file__).parent.parent / "logs" / "feedback.jsonl"

def log_feedback(question: str, answer: str, rating: str) -> None:
    _LOG_FILE.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer": answer,
        "rating": rating,
    }
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _set_rating(idx: int, rating: str, question: str, answer: str) -> None:
    st.session_state.history[idx]["rating"] = rating
    log_feedback(question, answer, rating)


# ---------------------------------------------------------------------------
# CACHED RESOURCE LOADER
#
# @st.cache_resource runs the function exactly once per app session and
# reuses the result on every rerun. This is important here because loading
# the FAISS index and the embedding model is slow (~2-3 seconds). Without
# caching, they would reload on every button click.
# ---------------------------------------------------------------------------
@st.cache_resource
def load_retriever():
    """Import retriever once and return the retrieve function."""
    return retrieve


# ---------------------------------------------------------------------------
# SESSION STATE
#
# st.session_state persists values across reruns (each button click causes
# a rerun). We store the full chat history here as a list of dicts.
# ---------------------------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.title("🐉 House of the Dragon Fandom Chat")
st.caption("Ask anything about the fandom — powered by Reddit discourse")
st.divider()


# ---------------------------------------------------------------------------
# CHAT HISTORY
#
# Loop through every past exchange and display it in order.
# Each entry has: question, answer, sources, off_topic, rating.
# ---------------------------------------------------------------------------
retrieve_fn = load_retriever()

for i, entry in enumerate(st.session_state.history):
    with st.chat_message("user"):
        st.write(entry["question"])

    with st.chat_message("assistant"):
        st.write(entry["answer"])

        if not entry.get("off_topic"):
            with st.expander("Sources"):
                for source in entry["sources"]:
                    st.markdown(f"- [{source['post_title']}]({source['url']})")

            # Feedback — show result if already rated, otherwise show buttons
            rating = entry.get("rating")
            if rating == "up":
                st.caption("👍 Marked as helpful")
            elif rating == "down":
                st.caption("👎 Marked as not helpful")
            else:
                col1, col2, _ = st.columns([1, 1, 8])
                with col1:
                    st.button(
                        "👍", key=f"up_{i}",
                        on_click=_set_rating,
                        args=(i, "up", entry["question"], entry["answer"]),
                    )
                with col2:
                    st.button(
                        "👎", key=f"down_{i}",
                        on_click=_set_rating,
                        args=(i, "down", entry["question"], entry["answer"]),
                    )


# ---------------------------------------------------------------------------
# INPUT FORM
#
# st.form groups the text input + button so that pressing Enter or clicking
# Submit both trigger the same action, and the form only reruns the app once
# (not on every keystroke).
# ---------------------------------------------------------------------------
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input(
        "Your question",
        placeholder="e.g. Who rides Caraxes?",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Ask")


# ---------------------------------------------------------------------------
# OFF-TOPIC MESSAGE
# ---------------------------------------------------------------------------
_OFF_TOPIC_REPLY = (
    "This chatbot is built specifically for **House of the Dragon** fandom discussion "
    "— it only knows what r/HouseOfTheDragon has talked about. I can't help with that one.\n\n"
    "Try asking something like:\n"
    "- *What does the fandom think of Daemon?*\n"
    "- *Who rides Caraxes?*\n"
    "- *How did people react to the season 2 finale?*"
)


# ---------------------------------------------------------------------------
# HANDLE SUBMIT
# ---------------------------------------------------------------------------
if submitted and user_input.strip():
    # Render the question immediately so the user sees it while we work
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Searching Reddit discourse and asking Claude..."):
            chunks = retrieve_fn(user_input)

            if is_off_topic(chunks):
                st.session_state.history.append({
                    "question": user_input,
                    "answer":   _OFF_TOPIC_REPLY,
                    "sources":  [],
                    "off_topic": True,
                    "rating":   None,
                })
            else:
                result = get_answer(user_input, chunks, history=st.session_state.history)
                st.session_state.history.append({
                    "question": user_input,
                    "answer":   result["answer"],
                    "sources":  result["sources"],
                    "off_topic": False,
                    "rating":   None,
                })

    st.rerun()
