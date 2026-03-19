import schedule
import time

from ai.generator import generate_best_posts
from whatsapp.sender import send_whatsapp_message
from utils.formatter import clean_text


# =========================
# RETRY CONFIG
# =========================

def retry_job(fn, retries=3, delay=3):
    """
    Retry wrapper for critical operations (e.g., OpenAI calls).

    - Retries the function if a transient error occurs
    - Uses exponential backoff to reduce pressure on external APIs
    - Raises exception only after all attempts fail

    This is essential for cloud environments (e.g., GitHub Actions),
    where network instability and timeouts are more common.
    """

    for attempt in range(retries):
        try:
            print(f"[INFO] Attempt {attempt+1}/{retries}")
            return fn()

        except Exception as e:
            print(f"[WARN] Attempt {attempt+1} failed: {e}")

            if attempt < retries - 1:
                sleep_time = delay * (2 ** attempt)  # exponential backoff
                print(f"[INFO] Retrying in {sleep_time}s...\n")
                time.sleep(sleep_time)

    raise Exception("Job failed after all retry attempts")


# =========================
# MAIN JOB
# =========================

def job():
    """
    Main scheduled job:
    - Generates best posts (AI + filtering + scoring)
    - Sends via WhatsApp (chunked + retry handled internally)

    Resilient to:
    - OpenAI connection issues
    - Temporary API failures
    - Network instability (cloud environments)
    """

    print("\n[INFO] Running scheduled job...\n")

    try:
        # 🔥 Critical part wrapped with retry (OpenAI calls inside)
        posts = retry_job(generate_best_posts)

        print(f"[INFO] Generated {len(posts)} posts.\n")

        for i, post in enumerate(posts, start=1):
            clean_post = clean_text(post)

            send_whatsapp_message(clean_post)

            print(f"[INFO] Post {i} sent successfully.\n")

            # Small delay to avoid hitting rate limits (Twilio / API)
            time.sleep(2)

        print("\n[SUCCESS] Job completed.\n")

    except Exception as e:
        print(f"[ERROR] Job failed after retries: {e}")


# =========================
# SCHEDULER CONFIG
# =========================

# Runs at 09:00 (server timezone — adjust if needed)
schedule.every().monday.at("09:00").do(job)
schedule.every().thursday.at("09:00").do(job)


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    # Run once immediately for testing (useful for local/dev)
    print("[INFO] Running test execution...\n")
    job()

    print("[INFO] Scheduler started...\n")

    while True:
        schedule.run_pending()
        time.sleep(60)