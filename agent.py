import os
import requests
from google import genai

# ================= CONFIGURATION (GITHUB SECRETS) =================
# We now pull these from GitHub's environment for security
GEMINI_KEY = os.environ.get("GEMINI_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
PDF_FILENAME = "book_chapter.pdf" 
# =================================================================

client = genai.Client(api_key=GEMINI_KEY)


def prepare_curriculum():
    """Reads the PDF and creates 4 daily lesson files."""
    print("🚀 Uploading PDF to Gemini...")
    uploaded_file = client.files.upload(file=PDF_FILENAME)

    prompt = """
    I am providing a chapter from a book. Please split this content into 4 distinct daily lessons.
    Each lesson must take approximately 8 minutes to read.

    STRICTLY use the 'Think-Sync' format for each day:
    🧠 Concept: [Name]

    📍 The Core: [1-sentence explanation]

    🧪 The Case: [The specific experiment/study]

    ⚠️ Why it trips you up: [System 1 vs 2 explanation]

    🏢 Real-World Example: [Modern scenario]

    🛠 The Antidote: [Question to ask yourself]

    🤳 Your Turn: [Reflective prompt]

    IMPORTANT: You MUST use HTML tags for formatting:
    - Use <b>Title</b> for bolding.
    - Use <i>text</i> for italics.

    CRITICAL INSTRUCTIONS FOR READABILITY:
    1. Add TWO empty lines between every section to create visual space.
    2. Do not include any intro/outro text.

    STRICT TEMPLATE:
    <b>🧠 Concept:</b> [Name]

    <b>📍 The Core:</b> [1-sentence explanation]

    <b>🧪 The Case:</b> [The experiment/study]

    <b>⚠️ Why it trips you up:</b> [System 1 vs 2]

    <b>🏢 Real-World Example:</b> [Modern scenario]

    <b>🛠 The Antidote:</b> [Question to ask]

    <b>🤳 Your Turn:</b> [Reflective prompt]

    IMPORTANT: You MUST put the text '---SPLIT---' (with the dashes)
    at the very end of Day 1, Day 2, and Day 3.

    Do not include any introductory text like 'Here are your lessons'.
    Start immediately with Day 1.
    """

    print("🧠 Generating 4-day plan...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[uploaded_file, prompt]
    )

    # Split the response into 4 parts and save to files
    lessons = response.text.split("---SPLIT---")
    for i, content in enumerate(lessons):
        if i < 4: # We only want 4 days
            filename = f"day_{i+1}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content.strip())

    # Initialize progress
    with open("progress.txt", "w") as f:
        f.write("1")

    print(f"✅ Created {len(lessons)} lesson files!")

def send_daily_lesson():
    """Reads the current day's file and sends it to Telegram."""
    if not os.path.exists("progress.txt"):
        print("❌ No curriculum found. Run prepare_curriculum() first.")
        return

    with open("progress.txt", "r") as f:
        current_day = int(f.read().strip())

    filename = f"day_{current_day}.txt"

    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            message = f.read()

        # Send to Telegram
        message = message.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        # Split message into chunks of 4000 characters to avoid Telegram's limit
        MAX_LENGTH = 4000
        parts = [message[i:i+MAX_LENGTH] for i in range(0, len(message), MAX_LENGTH)]

        for part in parts:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": part, "parse_mode": "HTML"}
            response = requests.post(url, data=payload)

        if response.status_code == 200:
            print(f"✅ Day {current_day} sent successfully!")
            # Update for tomorrow
            with open("progress.txt", "w") as f:
                f.write(str(current_day + 1))
        else:
            print(f"❌ Failed to send: {response.text}")
    else:
        print("🏁 All lessons for this chapter have been sent!")

if __name__ == "__main__":
    # IF RUNNING FOR THE FIRST TIME: Uncomment the line below to process your PDF
    prepare_curriculum()

    # FOR DAILY AUTOMATION: This is the function the scheduler will call
    send_daily_lesson()
