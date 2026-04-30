MOD_POST_KEYWORDS = [
    "premiere",
    "schedule",
    "megathread",
    "announcement",
    "pinned",
    "watch party",
    "episode thread",
    "discussion thread",
    "mod post",
    "weekly thread",
]

FILTER_RULES_POSTS = {
    "min_score": 100,
    "min_comments": 20,
    "exclude_removed": True,
    "exclude_deleted": True,
    "exclude_archived": True,
    "min_body_length": 50,
    "exclude_mod_posts": True,
}

FILTER_RULES_COMMENTS = {
    "min_score": 50,
    "max_per_post": 4,
    "exclude_removed": True,
    "exclude_deleted": True,
    "min_length": 30,
    "exclude_if_parent_deleted": True,
}


def filter_post(post, rules):
    if post.get("score", 0) < rules["min_score"]:
        return False

    if post.get("num_comments", 0) < rules["min_comments"]:
        return False

    body = post.get("selftext", "")

    if rules["exclude_removed"] and body == "[removed]":
        return False

    if rules["exclude_deleted"] and body == "[deleted]":
        return False

    if rules["exclude_archived"] and post.get("archived", False):
        return False

    if len(body.strip()) < rules["min_body_length"]:
        return False

    if rules.get("exclude_mod_posts"):
        title_lower = post.get("title", "").lower()
        if any(kw in title_lower for kw in MOD_POST_KEYWORDS):
            return False

    return True


def filter_comment(comment, rules):
    if comment.get("score", 0) < rules["min_score"]:
        return False

    body = comment.get("body", "")

    if rules["exclude_removed"] and body == "[removed]":
        return False

    if rules["exclude_deleted"] and body == "[deleted]":
        return False

    if len(body.strip()) < rules["min_length"]:
        return False

    if rules["exclude_if_parent_deleted"]:
        parent_body = comment.get("parent_body", "")
        if parent_body in ["[deleted]", "[removed]"]:
            return False

    return True
