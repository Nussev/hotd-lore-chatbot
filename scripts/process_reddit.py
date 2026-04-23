import orjson
from tqdm import tqdm
import os

#-------------------
# FILE PATHS
#-------------------
INPUT_FILE = os.path.join("data_raw", "r_HouseOfTheDragon_posts.jsonl")
OUTPUT_FILE = os.path.join("data_clean", "hotd_clean_posts.txt")

#-------------------
# FILTER SETTINGS
#-------------------
MIN_SCORE = 100  # Minimum upvotes to consider a post "high quality"
MIN_COMMENTS = 20  # Minimum number of comments to consider a post "engaging"

#-------------------
# VALIDATION FUNCTION
#-------------------
def is_valid_post(post):
    """
    Filters out low-quality or irrelevant posts
    """
    if post.get("score", 0) < MIN_SCORE:
        return False
    if post.get("num_comments", 0) < MIN_COMMENTS:
        return False

    selftext = post.get("selftext:, "")

    if selftext in ["[deleted]", "[removed]", ""]:
        return False

    return True

#-------------------
# MAIN PIPELINE
#-------------------
os.makedirs("data_clean", exist_ok=True)

