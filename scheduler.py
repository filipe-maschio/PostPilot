import schedule
import time

from ai.generator import generate_best_posts
from whatsapp.sender import send_whatsapp_message
from utils.formatter import clean_text


def job():
    """
    Main scheduled job:
    - Generates best posts (already filtered and scored)
    - Sends via WhatsApp
    """

    print("\n[INFO] Running scheduled job...\n")

    try:
        posts = generate_best_posts()
        print(f"[INFO] Generated {len(posts)} posts.\n")

        for i, post in enumerate(posts, start=1):
            clean_post = clean_text(post)

            send_whatsapp_message(clean_post)

            print(f"[INFO] Post {i} sent successfully.\n")

            time.sleep(2)

        print("\n[SUCCESS] Job completed.\n")

    except Exception as e:
        print(f"[ERROR] Job failed: {e}")


# =========================
# SCHEDULER CONFIG
# =========================

schedule.every().monday.at("09:00").do(job)
schedule.every().thursday.at("09:00").do(job)


if __name__ == "__main__":
    # Run once immediately for testing
    print("[INFO] Running test execution...\n")
    job()

    print("[INFO] Scheduler started...\n")

    while True:
        schedule.run_pending()
        time.sleep(60)