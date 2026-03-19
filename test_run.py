from ai.generator import generate_best_posts
from utils.formatter import clean_text
from whatsapp.sender import send_whatsapp_message


def run_test():
    print("\nStarting local test...\n")

    posts = generate_best_posts()

    print(f"Generated {len(posts)} posts\n")

    for i, post in enumerate(posts, start=1):
        print(f"\n--- POST {i} (RAW) ---\n")
        print(post)

        clean_post = clean_text(post)

        print(f"\n--- POST {i} (CLEAN) ---\n")
        print(clean_post)

        print("\n📤 Sending via WhatsApp...\n")
        send_whatsapp_message(clean_post)

    print("\n✅ TEST COMPLETED\n")


if __name__ == "__main__":
    run_test()