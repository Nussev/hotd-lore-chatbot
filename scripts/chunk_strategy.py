def get_top_comments(comment_list, n=4, min_score=50):
    eligible = [
        c for c in comment_list
        if c.get("score", 0) >= min_score
        and c.get("body", "") not in ["[deleted]", "[removed]", ""]
    ]
    eligible.sort(key=lambda c: c.get("score", 0), reverse=True)
    return eligible[:n]


def create_chunk(post, comments):
    post_id = post.get("id", "")
    title = post.get("title", "").strip()
    body = post.get("selftext", "").strip()

    top_comments = get_top_comments(comments)

    comment_lines = "\n".join(
        f"- {c.get('body', '').strip()}" for c in top_comments
    )

    if comment_lines:
        full_text = f"{title}\n\n{body}\n\n--- Top Comments ---\n{comment_lines}"
    else:
        full_text = f"{title}\n\n{body}"

    char_count = len(full_text)

    return {
        "chunk_id": f"post_{post_id}_v1",
        "source_type": "post_with_comments",
        "primary": {
            "text": full_text,
            "char_count": char_count,
            "token_estimate": char_count // 4,
        },
        "metadata": {
            "post_id": post_id,
            "post_title": title,
            "post_author": post.get("author", ""),
            "post_score": post.get("score", 0),
            "post_comments": post.get("num_comments", 0),
            "created_utc": post.get("created_utc", 0),
            "subreddit": post.get("subreddit", ""),
        },
        "components": {
            "post_body_chars": len(body),
            "num_comments_included": len(top_comments),
            "top_comment_scores": [c.get("score", 0) for c in top_comments],
        },
        "quality": {
            "is_removed": body == "[removed]",
            "is_deleted": body == "[deleted]",
        },
    }
