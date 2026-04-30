import argparse
import os
import sys
import orjson
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.filters import FILTER_RULES_POSTS, filter_post
from chunk_strategy import create_chunk

# ----------------------------
# FILE PATHS
# ----------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_POSTS    = os.path.join(ROOT, "data_raw", "r_HouseOfTheDragon_posts.jsonl")
INPUT_COMMENTS = os.path.join(ROOT, "data_raw", "r_HouseOfTheDragon_comments.jsonl")
OUTPUT_FILE    = os.path.join(ROOT, "data_clean", "hotd_chunks.jsonl")


# ----------------------------
# HELPERS
# ----------------------------
def clean_text(text):
    if not text:
        return ""
    return text.replace("\n", " ").replace("\r", " ").strip()


def group_comments_by_post(comments_path):
    """Loads comments JSONL, groups by post_id, sorts each group by score desc."""
    groups = {}

    if not os.path.exists(comments_path):
        print(f"[WARN] Comments file not found: {comments_path}. Proceeding without comments.")
        return groups

    print(f"Loading comments from: {comments_path}")
    with open(comments_path, "r", encoding="utf-8") as f:
        for line in tqdm(f, desc="Loading comments"):
            line = line.strip()
            if not line:
                continue
            try:
                comment = orjson.loads(line)
            except Exception:
                continue

            # parent_id format is "t3_<post_id>" for top-level comments
            parent_id = comment.get("parent_id", "")
            if not parent_id.startswith("t3_"):
                continue

            post_id = parent_id[3:]
            if post_id not in groups:
                groups[post_id] = []
            groups[post_id].append(comment)

    for post_id in groups:
        groups[post_id].sort(key=lambda c: c.get("score", 0), reverse=True)

    print(f"Grouped comments for {len(groups)} posts.\n")
    return groups


# ----------------------------
# MAIN PIPELINE
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="Process Reddit posts into RAG-ready chunks.")
    parser.add_argument("--limit", type=int, default=None, help="Max posts to process (for test runs)")
    args = parser.parse_args()

    os.makedirs(os.path.join(ROOT, "data_clean"), exist_ok=True)

    comments_by_post = group_comments_by_post(INPUT_COMMENTS)

    posts_loaded = 0
    posts_passed = 0
    chunks_written = 0

    print(f"Processing posts from : {INPUT_POSTS}")
    print(f"Output                : {OUTPUT_FILE}\n")

    with open(INPUT_POSTS, "r", encoding="utf-8") as infile, \
         open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:

        for line in infile:
            line = line.strip()
            if not line:
                continue

            try:
                post = orjson.loads(line)
            except Exception:
                continue

            if post.get("subreddit") != "HouseOfTheDragon":
                continue

            posts_loaded += 1

            if not filter_post(post, FILTER_RULES_POSTS):
                continue

            posts_passed += 1

            post["title"]    = clean_text(post.get("title"))
            post["selftext"] = clean_text(post.get("selftext"))

            post_id  = post.get("id", "")
            comments = comments_by_post.get(post_id, [])

            chunk = create_chunk(post, comments)
            outfile.write(orjson.dumps(chunk).decode() + "\n")
            chunks_written += 1

            if args.limit and chunks_written >= args.limit:
                break

            if chunks_written % 100 == 0:
                print(f"  Progress: {chunks_written} chunks written...")

    print("\n" + "=" * 50)
    print("  PIPELINE COMPLETE")
    print("=" * 50)
    print(f"  Posts loaded (HOTD only) : {posts_loaded}")
    print(f"  Posts passed filter      : {posts_passed}")
    print(f"  Chunks written           : {chunks_written}")
    print(f"  Output                   : {OUTPUT_FILE}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
