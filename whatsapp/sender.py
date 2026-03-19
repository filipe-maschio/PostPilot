from twilio.rest import Client
import os
from dotenv import load_dotenv
import time

# =========================
# ENVIRONMENT SETUP
# =========================

# Load environment variables from .env (local only)
load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_SID")
AUTH_TOKEN = os.getenv("TWILIO_TOKEN")
FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER")
TO_WHATSAPP = os.getenv("MY_WHATSAPP_NUMBER")

# Validate required environment variables (fail fast)
if not all([ACCOUNT_SID, AUTH_TOKEN, FROM_WHATSAPP, TO_WHATSAPP]):
    raise ValueError("Missing Twilio environment variables")

# Initialize Twilio client
client = Client(ACCOUNT_SID, AUTH_TOKEN)

MAX_LENGTH = 1500


# =========================
# RETRY MECHANISM
# =========================

def send_with_retry(send_function, retries=3, delay=2):
    """
    Retry wrapper for network calls (e.g., Twilio API).

    Args:
        send_function (callable): Function that performs the API call
        retries (int): Number of retry attempts
        delay (int): Delay between retries (seconds)

    Raises:
        Exception: If all retries fail
    """
    for attempt in range(retries):
        try:
            return send_function()
        except Exception as e:
            print(f"[WARN] Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)

    raise Exception("Failed after retries")


# =========================
# MESSAGE SPLITTING
# =========================

def split_message(text, max_length=MAX_LENGTH):
    """
    Split message into chunks while preserving line breaks.

    This ensures messages respect Twilio's size limits.
    """
    chunks = []
    current_chunk = ""

    lines = text.split("\n")

    for line in lines:
        candidate = (current_chunk + "\n" + line).strip() if current_chunk else line

        if len(candidate) <= max_length:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


# =========================
# MAIN SEND FUNCTION
# =========================

def send_whatsapp_message(content):
    """
    Send a WhatsApp message using Twilio API.

    - Splits long messages into chunks
    - Uses retry mechanism for network reliability
    - Logs success and failure per chunk
    """

    chunks = split_message(content)

    for i, chunk in enumerate(chunks, start=1):
        try:
            message = send_with_retry(lambda: client.messages.create(
                body=chunk,
                from_=f"{FROM_WHATSAPP}",
                to=f"{TO_WHATSAPP}"
            ))

            print(f"[INFO] Chunk {i} sent. SID: {message.sid}")

        except Exception as e:
            print(f"[ERROR] Failed to send chunk {i}: {e}")