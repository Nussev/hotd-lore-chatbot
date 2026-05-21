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
  background: linear-gradient(160deg, #0a0a28 0%, #0e0e38 60%, #080820 100%);
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

DRAGON_IDLE_HTML = """
<style>
@keyframes d-breathe {
  0%, 100% { transform: translateY(0px)   scale(1);    }
  50%       { transform: translateY(-2px) scale(1.025); }
}
@keyframes d-blink {
  0%, 90%, 100% { transform: scaleY(1);   }
  95%            { transform: scaleY(0.1); }
}
@keyframes d-wing-sway {
  0%, 100% { transform: rotate(0deg);  }
  50%       { transform: rotate(-6deg); }
}
</style>
<div style="display:flex;justify-content:center;margin:8px 0 4px;">
<div style="background:#0a0a14;border-radius:10px;padding:18px 24px;display:inline-block;">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 120" width="168" height="144">
  <g style="transform-origin:100px 90px; animation: d-breathe 3.8s ease-in-out infinite;">
    <g style="transform-origin:105px 70px; animation: d-wing-sway 3.8s ease-in-out infinite;">
      <path d="M105 70 Q118 48 130 52 Q128 60 122 66 Q130 58 132 68 Q126 65 120 72 Q128 64 128 74 Q120 70 112 76Z"
            fill="#5a0000" opacity="0.85"/>
    </g>
    <path d="M88 118 Q95 100 100 82 Q100 74 94 68" stroke="#8B0000" stroke-width="18"
          fill="none" stroke-linecap="round"/>
    <path d="M82 118 Q90 100 94 82 Q94 74 90 70" stroke="#a83030" stroke-width="7"
          fill="none" stroke-linecap="round"/>
    <path d="M97 88 L103 80 M100 76 L107 68 M102 68 L108 60"
          stroke="#6a0000" stroke-width="2.5" stroke-linecap="round" fill="none"/>
    <path d="M94 68 Q90 56 82 48 Q70 38 52 32 Q34 26 18 30 Q6 35 4 46 Q2 56 8 64
             Q14 72 28 74 Q50 78 70 72 Q84 68 94 68Z" fill="#8B0000"/>
    <path d="M18 30 Q36 22 55 28 Q70 32 82 42"
          stroke="#5a0000" stroke-width="5" fill="none" stroke-linecap="round"/>
    <path d="M22 36 Q38 30 56 34 Q68 38 78 46"
          stroke="#6e1010" stroke-width="3" fill="none" stroke-linecap="round"/>
    <ellipse cx="7" cy="50" rx="6" ry="8" fill="#7a0000"/>
    <path d="M54 28 Q50 14 44 8 Q50 16 58 24" fill="#3d0000"/>
    <path d="M66 30 Q64 18 60 14 Q65 20 68 28" fill="#3d0000"/>
    <ellipse cx="36" cy="40" rx="8" ry="7" fill="#3d0000"/>
    <ellipse cx="36" cy="40" rx="6" ry="5.5" fill="#FFD700"/>
    <g style="transform-origin:36px 40px; animation: d-blink 5s ease-in-out infinite;">
      <ellipse cx="36" cy="40" rx="2.2" ry="5.2" fill="#0d0000"/>
    </g>
    <circle cx="33" cy="37" r="1.2" fill="rgba(255,255,220,0.6)"/>
    <ellipse cx="6" cy="46" rx="2" ry="1.5" fill="#4a0000" transform="rotate(-15,6,46)"/>
    <path d="M12 72 L14 80 M19 74 L20 83 M26 75 L27 84 M33 75 L34 83 M40 74 L40 82"
          stroke="#ddd8c8" stroke-width="2.8" stroke-linecap="round" fill="none"/>
    <g style="transform-origin:88px 68px;">
      <path d="M88 68 Q80 74 62 78 Q42 82 22 80 Q10 78 6 72 Q2 66 6 62
               Q10 68 24 70 Q46 74 66 70 Q80 67 88 68Z" fill="#7a1010"/>
      <path d="M8 68 Q5 74 10 78 Q26 86 50 84 Q68 82 82 74"
            stroke="#5a0808" stroke-width="3" fill="none" stroke-linecap="round"/>
      <path d="M16 70 L15 62 M23 72 L22 63 M30 73 L29 64 M37 73 L36 65 M44 72 L43 64"
            stroke="#ddd8c8" stroke-width="2.4" stroke-linecap="round" fill="none"/>
    </g>
  </g>
</svg>
</div>
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
st.title("🐉 The Maester's Archive")
st.caption("Consult the scrolls — drawn from the fandom's own words")
st.divider()

st.markdown(DRAGON_IDLE_HTML, unsafe_allow_html=True)

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
