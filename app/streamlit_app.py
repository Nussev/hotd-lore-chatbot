import sys
import os

# Make the project root importable so "from rag.retriever import ..." works
# regardless of where Streamlit is launched from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from rag.retriever import retrieve
from rag.chat import get_answer

# ---------------------------------------------------------------------------
# PAGE CONFIG
# st.set_page_config must be the very first Streamlit call in the script.
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="HOTD Fandom Chat",
    page_icon="🐉",
    layout="centered",
)

# ---------------------------------------------------------------------------
# CACHED RESOURCE LOADER
#
# @st.cache_resource runs the function exactly once per app session and
# reuses the result on every rerun. This is important here because loading
# the FAISS index and the embedding model is slow (~2-3 seconds). Without
# caching, they would reload on every button click.
#
# We "load" the retriever simply by importing it — retriever.py does all its
# loading at module level, so importing it is enough to trigger it once.
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
# Each entry in history has: question, answer, sources.
# ---------------------------------------------------------------------------
retrieve_fn = load_retriever()

for entry in st.session_state.history:
    # User message
    with st.chat_message("user"):
        st.write(entry["question"])

    # Assistant answer
    with st.chat_message("assistant"):
        st.write(entry["answer"])

        # Sources collapsed by default so they don't clutter the UI
        with st.expander("Sources"):
            for source in entry["sources"]:
                # st.markdown lets us render a clickable hyperlink
                st.markdown(f"- [{source['post_title']}]({source['url']})")


# ---------------------------------------------------------------------------
# INPUT FORM
#
# st.form groups the text input + button so that pressing Enter or clicking
# Submit both trigger the same action, and the form only reruns the app once
# (not on every keystroke).
# ---------------------------------------------------------------------------
with st.form(key="chat_form", clear_on_submit=True):
    # clear_on_submit=True empties the text box after the user submits
    user_input = st.text_input(
        "Your question",
        placeholder="e.g. Who rides Caraxes?",
        label_visibility="collapsed",  # hides the label text, keeps it clean
    )
    submitted = st.form_submit_button("Ask")


# ---------------------------------------------------------------------------
# HANDLE SUBMIT
# ---------------------------------------------------------------------------
if submitted and user_input.strip():
    # Show a spinner while we embed the query, search FAISS, and call Claude
    with st.spinner("Searching Reddit discourse and asking Claude..."):
        chunks = retrieve_fn(user_input)
        result = get_answer(user_input, chunks, history=st.session_state.history)

    # Save this exchange to history so it renders on the next rerun
    st.session_state.history.append({
        "question": user_input,
        "answer":   result["answer"],
        "sources":  result["sources"],
    })

    # Rerun the app so the new message appears in the chat history above
    st.rerun()
