import json
import os

POSTS_FILE = "data/posts.json"
THEMES_FILE = "data/themes.json"

MAX_POSTS = 20
MAX_THEMES = 30


# =========================
# POSTS STORAGE
# =========================

def load_posts():
    """
    Load stored posts from JSON file.

    If the file does not exist, it is automatically created.

    Returns:
        list: List of stored posts (empty if newly created).
    """
    if not os.path.exists(POSTS_FILE):
        os.makedirs("data", exist_ok=True)
        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_post_with_metadata(post, scores):
    """
    Save a post along with its AI evaluation metadata.

    This replaces the old save_post() approach.
    Each entry contains:
    - raw post content
    - final score
    - individual scoring criteria
    """

    posts = load_posts()

    entry = {
        "post": post,
        "score": scores.get("final", 5.0),
        "hook": scores.get("hook", 5.0),
        "clarity": scores.get("clareza", 5.0),
        "value": scores.get("valor", 5.0),
        "originality": scores.get("originalidade", 5.0),
        "engagement": scores.get("engajamento", 5.0),
    }

    posts.append(entry)

    # Keep only the most recent posts
    posts = posts[-MAX_POSTS:]

    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


# =========================
# THEMES STORAGE
# =========================

def load_themes():
    """
    Load stored themes from JSON file.

    If the file does not exist, it is automatically created
    along with the required directory structure.

    Returns:
        list: List of stored themes (empty if newly created).
    """
    if not os.path.exists(THEMES_FILE):
        os.makedirs("data", exist_ok=True)
        with open(THEMES_FILE, "w") as f:
            json.dump([], f)
        return []

    with open(THEMES_FILE, "r") as f:
        return json.load(f)


def save_theme(theme):
    """
    Save a theme if it does not already exist.
    Keeps only the most recent themes.
    """
    themes = load_themes()

    if theme not in themes:
        themes.append(theme)

    themes = themes[-MAX_THEMES:]

    with open(THEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(themes, f, ensure_ascii=False, indent=2)