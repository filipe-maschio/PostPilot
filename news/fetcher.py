import feedparser
import random
import re

RSS_FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://krebsonsecurity.com/feed/",
    "https://www.bleepingcomputer.com/feed/"
]


def clean_html(raw_html):
    clean_text = re.sub(r"<.*?>", "", raw_html)
    clean_text = re.sub(r"\s+", " ", clean_text)
    return clean_text.strip()


def truncate_text(text, max_length=300):
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    last_space = truncated.rfind(" ")

    return truncated[:last_space] if last_space != -1 else truncated


def get_cybersecurity_news():
    feed_url = random.choice(RSS_FEEDS)
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        return {
            "title": "No news available",
            "summary": "Unable to fetch cybersecurity news.",
            "link": ""
        }

    entries = feed.entries[:10]  # prioritize recent news
    entry = random.choice(entries)

    title = entry.get("title", "No title")

    raw_summary = entry.get("summary", "")
    clean_summary = clean_html(raw_summary)

    if len(clean_summary) < 50:
        return get_cybersecurity_news()

    clean_summary = truncate_text(clean_summary)

    return {
        "title": title,
        "summary": clean_summary,
        "link": entry.get("link", "")
    }