import json
from datetime import datetime

from core.config import FEEDBACK_LOG


def log_feedback(question: str, answer: str, rating: str) -> None:
    """Append a single feedback entry to the JSONL log file."""
    FEEDBACK_LOG.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "question": question,
        "answer": answer,
        "rating": rating,
    }
    with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
