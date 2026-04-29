import orjson
from tqdm import tqdm
import os

#-------------------
# FILE PATHS
#-------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_FILE = os.path.join(ROOT, "data_raw", "r_HouseOfTheDragon_posts.jsonl")
OUTPUT_FILE = os.path.join(ROOT, "data_clean", "hotd_clean_posts.txt")

# -----------------------------
# FILTER SETTINGS
# -----------------------------
MIN_SCORE = 100
MIN_COMMENTS = 20

# -----------------------------
# TEXT CLEANING FUNCTION
# -----------------------------
def clean_text(text):
    """
    Cleans raw Reddit text by:
    - removing None values
    - stripping whitespace
    - removing newline characters
    """
    if not text:
        return ""

    return text.replace("\n", " ").replace("\r", " ").strip()

# -----------------------------
# VALIDATION FUNCTION
# -----------------------------
def is_valid_post(post):
    """
    Filters out low-quality or irrelevant posts
    """
    if post.get("score", 0) < MIN_SCORE:
        return False

    if post.get("num_comments", 0) < MIN_COMMENTS:
        return False

    selftext = post.get("selftext", "")

    if selftext in ["[deleted]", "[removed]", ""]:
        return False

    return True

# -----------------------------
# MAIN PIPELINE
# -----------------------------
os.makedirs("data_clean", exist_ok=True)

with open(INPUT_FILE, "r", encoding="utf-8") as infile, \
     open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

    for line in tqdm(infile):

        try:
            post = orjson.loads(line)
        except:
            continue  # skip bad lines

        # ONLY keep HOTD subreddit posts
        if post.get("subreddit") != "HouseOfTheDragon":
            continue

        # apply quality filter
        if not is_valid_post(post):
            continue

        # -----------------------------
        # CLEAN FIELDS
        # -----------------------------
        title = clean_text(post.get("title"))
        body = clean_text(post.get("selftext"))

        score = post.get("score", 0)

        # -----------------------------
        # SIMPLE TAGGING SYSTEM
        # -----------------------------
        text_blob = (title + " " + body).lower()

        tags = []

        for keyword in [
            "daemon",
            "rhaenyra",
            "alicent",
            "aegon",
            "viserys",
            "dragon",
            "succession"
        ]:
            if keyword in text_blob:
                tags.append(keyword)

        # -----------------------------
        # WRITE CLEAN OUTPUT
        # -----------------------------
        outfile.write(f"TITLE: {title}\n")
        outfile.write(f"SCORE: {score}\n")
        outfile.write(f"TAGS: {', '.join(tags)}\n")
        outfile.write(f"POST: {body}\n")
        outfile.write("\n" + "=" * 80 + "\n\n")