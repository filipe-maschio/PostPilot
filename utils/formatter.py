import re


def clean_text(text):
    """
    Clean text for safe usage (WhatsApp, storage, LinkedIn).

    - Removes emojis
    - Removes extra spaces
    - Normalizes line breaks
    """

    # Remove emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)

    # Remove excessive line breaks (more than 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove trailing spaces on each line
    text = "\n".join(line.strip() for line in text.splitlines())

    # Remove leading/trailing spaces
    text = text.strip()

    return text