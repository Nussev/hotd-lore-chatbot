from dotenv import load_dotenv
import anthropic

load_dotenv()

# Single shared Anthropic client — constructed once at import time, reused
# across all calls. Reads ANTHROPIC_API_KEY from the environment (.env locally,
# Streamlit Cloud secrets in production).
client = anthropic.Anthropic()
