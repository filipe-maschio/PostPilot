from ai.generator import generate_best_posts
from utils.formatter import clean_text
from whatsapp.sender import send_whatsapp_message


def main():
    print("\n[INFO] Generating posts...\n")

    posts = generate_best_posts()

    if not posts:
        print("[WARNING] No posts generated.")
        return

    for i, post in enumerate(posts, start=1):
        print(f"\n[INFO] Processing post {i}...\n")

        clean_post = clean_text(post).strip()

        if not clean_post:
            print(f"[WARNING] Post {i} is empty. Skipping.")
            continue

        try:
            send_whatsapp_message(clean_post)
            print(f"[SUCCESS] Post {i} sent to WhatsApp.")
        except Exception as e:
            print(f"[ERROR] Failed to send post {i}: {e}")

        print("\n--- GENERATED POST ---\n")
        print(clean_post)


if __name__ == "__main__":
    main()