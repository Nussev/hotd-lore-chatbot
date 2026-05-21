import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from rag.retriever import retrieve, is_off_topic
from rag.chat import get_answer
from core.config import OFF_TOPIC_REPLY
from core.feedback import log_feedback

# ---------------------------------------------------------------------------
# ANIMATION HTML CONSTANTS
# ---------------------------------------------------------------------------
RAVENS_HTML = """
<style>
@keyframes wingflap {
  0%   { transform: rotate(-24deg) translateY(2px);  }
  100% { transform: rotate(18deg)  translateY(-2px); }
}
@keyframes flyacross {
  0%   { left: -90px; opacity: 0; }
  5%   { opacity: 1; }
  92%  { opacity: 1; }
  100% { left: calc(100% + 90px); opacity: 0; }
}
.raven-stage {
  position: relative;
  height: 160px;
  background: linear-gradient(160deg, #1c1c3a 0%, #232345 60%, #181830 100%);
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 6px;
}
.raven-stage::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    radial-gradient(1px 1px at 15% 20%, rgba(200,150,12,0.4) 0%, transparent 100%),
    radial-gradient(1px 1px at 40% 12%, rgba(255,255,255,0.25) 0%, transparent 100%),
    radial-gradient(1px 1px at 65% 30%, rgba(255,255,255,0.2) 0%, transparent 100%),
    radial-gradient(1px 1px at 80% 10%, rgba(200,150,12,0.3) 0%, transparent 100%),
    radial-gradient(1px 1px at 25% 75%, rgba(255,255,255,0.15) 0%, transparent 100%),
    radial-gradient(1px 1px at 90% 60%, rgba(255,255,255,0.2) 0%, transparent 100%),
    radial-gradient(1px 1px at 55% 80%, rgba(200,150,12,0.25) 0%, transparent 100%);
}
.raven-wrap {
  position: absolute;
  filter: drop-shadow(0 0 3px rgba(200,150,12,0.55)) drop-shadow(0 0 6px rgba(180,120,8,0.25));
}
.r1 { top: 28%; animation: flyacross 4.2s linear 0.0s infinite; }
.r2 { top: 55%; animation: flyacross 5.1s linear 1.7s infinite; }
.r3 { top: 16%; animation: flyacross 4.7s linear 0.9s infinite; }
.r3 svg { transform: scale(0.75); transform-origin: left center; }
.wing1 { transform-origin: 38px 26px; animation: wingflap 0.33s ease-in-out 0.00s infinite alternate; }
.wing2 { transform-origin: 38px 26px; animation: wingflap 0.33s ease-in-out 0.11s infinite alternate; }
.wing3 { transform-origin: 38px 26px; animation: wingflap 0.33s ease-in-out 0.19s infinite alternate; }
.raven-label {
  position: absolute;
  bottom: 12px;
  width: 100%;
  text-align: center;
  color: #c8960c;
  font-family: Georgia, serif;
  font-style: italic;
  font-size: 13px;
  letter-spacing: 0.6px;
  opacity: 0.9;
}
</style>
<div class="raven-stage">
  <div class="raven-wrap r1">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 55" width="74" height="41">
      <ellipse cx="45" cy="33" rx="20" ry="11" fill="#080808"/>
      <ellipse cx="64" cy="27" rx="11" ry="10" fill="#080808"/>
      <path d="M73 25 Q82 27 80 32 Q77 29 73 28 Z" fill="#080808"/>
      <polygon points="25,31 3,22 3,40" fill="#080808"/>
      <g class="wing1"><path d="M40 27 Q28 8 58 13 Q63 15 52 25" fill="#111"/></g>
      <circle cx="68" cy="25" r="1.8" fill="#c8960c"/>
    </svg>
  </div>
  <div class="raven-wrap r2">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 55" width="74" height="41">
      <ellipse cx="45" cy="33" rx="20" ry="11" fill="#080808"/>
      <ellipse cx="64" cy="27" rx="11" ry="10" fill="#080808"/>
      <path d="M73 25 Q82 27 80 32 Q77 29 73 28 Z" fill="#080808"/>
      <polygon points="25,31 3,22 3,40" fill="#080808"/>
      <g class="wing2"><path d="M40 27 Q28 8 58 13 Q63 15 52 25" fill="#111"/></g>
      <circle cx="68" cy="25" r="1.8" fill="#c8960c"/>
    </svg>
  </div>
  <div class="raven-wrap r3">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 55" width="74" height="41">
      <ellipse cx="45" cy="33" rx="20" ry="11" fill="#080808"/>
      <ellipse cx="64" cy="27" rx="11" ry="10" fill="#080808"/>
      <path d="M73 25 Q82 27 80 32 Q77 29 73 28 Z" fill="#080808"/>
      <polygon points="25,31 3,22 3,40" fill="#080808"/>
      <g class="wing3"><path d="M40 27 Q28 8 58 13 Q63 15 52 25" fill="#111"/></g>
      <circle cx="68" cy="25" r="1.8" fill="#c8960c"/>
    </svg>
  </div>
  <div class="raven-label">The ravens carry your message...</div>
</div>
"""


# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="The Maester's Archive",
    page_icon="🐉",
    layout="centered",
)

# ---------------------------------------------------------------------------
# FEEDBACK CALLBACK
# Streamlit on_click callbacks must live in the app layer because they touch
# st.session_state. log_feedback() (the pure write) lives in core/feedback.py.
# ---------------------------------------------------------------------------
def _set_rating(idx: int, rating: str, question: str, answer: str) -> None:
    st.session_state.history[idx]["rating"] = rating
    log_feedback(question, answer, rating)


_HOUSE_CONFIG = {
    "black": {
        "seal":    "#6b0e1e",
        "label":   "🖤 Team Black — Rhaenyra Targaryen",
        "caption": "Fire and Blood. The realm is hers by right.",
        "badge_bg": "#3a0810",
        "badge_text": "#e8b4bc",
    },
    "green": {
        "seal":    "#1e4d16",
        "label":   "💚 Team Green — Alicent Hightower",
        "caption": "Duty and honour. The realm must have order.",
        "badge_bg": "#112b0a",
        "badge_text": "#a8d4a0",
    },
}


def _source_card_html(source: dict, house: str) -> str:
    cfg = _HOUSE_CONFIG[house]
    score = source.get("post_score", 0)
    title = source.get("post_title", "Untitled")
    url   = source.get("url", "#")
    return (
        f'<div style="background:linear-gradient(135deg,#1e1a0e 0%,#2a2415 100%);'
        f'border:1px solid #6b5a2e;border-radius:8px;padding:12px 14px;'
        f'margin:6px 0;display:flex;align-items:center;gap:12px;">'
        f'<div style="min-width:44px;height:44px;background:{cfg["seal"]};'
        f'border-radius:50%;display:flex;align-items:center;justify-content:center;'
        f'font-size:11px;font-weight:bold;color:#fff;font-family:Georgia,serif;'
        f'box-shadow:0 2px 6px rgba(0,0,0,0.6);flex-shrink:0;'
        f'border:2px solid rgba(255,255,255,0.15);">{score}</div>'
        f'<a href="{url}" target="_blank" style="color:#d4c07a;font-family:Georgia,serif;'
        f'font-size:13px;text-decoration:none;line-height:1.45;">{title}</a>'
        f'</div>'
    )


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
if "house" not in st.session_state:
    st.session_state.house = "black"


# ---------------------------------------------------------------------------
# SIDEBAR — HOUSE SELECTOR
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚔️ Choose Your House")
    selected = st.radio(
        "house",
        options=list(_HOUSE_CONFIG.keys()),
        format_func=lambda h: _HOUSE_CONFIG[h]["label"],
        index=list(_HOUSE_CONFIG.keys()).index(st.session_state.house),
        label_visibility="collapsed",
    )
    if selected != st.session_state.house:
        st.session_state.house = selected
        st.rerun()
    cfg = _HOUSE_CONFIG[st.session_state.house]
    st.caption(cfg["caption"])


# ---------------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------------
st.title("🐉 The Maester's Archive")
st.caption("Consult the scrolls — drawn from the fandom's own words")

cfg = _HOUSE_CONFIG[st.session_state.house]
st.markdown(
    f'<div style="display:inline-block;background:{cfg["badge_bg"]};'
    f'color:{cfg["badge_text"]};padding:3px 12px;border-radius:12px;'
    f'font-size:12px;font-family:Georgia,serif;margin-bottom:4px;">'
    f'{cfg["label"]}</div>',
    unsafe_allow_html=True,
)
st.divider()

if not st.session_state.history:
    st.markdown("*The ravens have returned. Ask your question and the archive shall answer.*")


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
        st.markdown("*~ The Maester consults the scrolls ~*")
        st.write(entry["answer"])

        if not entry.get("off_topic"):
            with st.expander("📜 Scrolls consulted"):
                for source in entry["sources"]:
                    st.markdown(
                        _source_card_html(source, st.session_state.house),
                        unsafe_allow_html=True,
                    )

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
        placeholder="What do you wish to know, my lord?",
        label_visibility="collapsed",
    )
    submitted = st.form_submit_button("Send Raven")


# ---------------------------------------------------------------------------
# HANDLE SUBMIT
# ---------------------------------------------------------------------------
if submitted and user_input.strip():
    # Render the question immediately so the user sees it while we work
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        _loading = st.empty()
        _loading.markdown(RAVENS_HTML, unsafe_allow_html=True)

        chunks = retrieve_fn(user_input)
        off_topic = is_off_topic(chunks)
        if not off_topic:
            result = get_answer(user_input, chunks, history=st.session_state.history)

        _loading.empty()

        if off_topic:
            st.session_state.history.append({
                "question": user_input,
                "answer":   OFF_TOPIC_REPLY,
                "sources":  [],
                "off_topic": True,
                "rating":   None,
            })
        else:
            st.session_state.history.append({
                "question": user_input,
                "answer":   result["answer"],
                "sources":  result["sources"],
                "off_topic": False,
                "rating":   None,
            })

    st.rerun()
