from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ACCOUNT_SID = os.getenv("TWILIO_SID")
AUTH_TOKEN = os.getenv("TWILIO_TOKEN")
FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER")
TO_WHATSAPP = os.getenv("MY_WHATSAPP_NUMBER")

# Validate environment variables
if not all([ACCOUNT_SID, AUTH_TOKEN, FROM_WHATSAPP, TO_WHATSAPP]):
    raise ValueError("Missing Twilio environment variables")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

MAX_LENGTH = 1500


def split_message(text, max_length=MAX_LENGTH):
    """
    Split message into chunks while preserving line breaks.
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


def send_whatsapp_message(content):
    """
    Send a WhatsApp message using Twilio API.
    Assumes content is already cleaned before calling this function.
    """

    chunks = split_message(content)

    for i, chunk in enumerate(chunks, start=1):
        try:
            message = client.messages.create(
                body=chunk,
                from_=f"whatsapp:{FROM_WHATSAPP}",
                to=f"whatsapp:{TO_WHATSAPP}"
            )

            print(f"[INFO] Chunk {i} sent. SID: {message.sid}")

        except Exception as e:
            print(f"[ERROR] Failed to send chunk {i}: {e}")