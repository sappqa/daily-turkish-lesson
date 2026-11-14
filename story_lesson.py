import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


# Files
BASE_DIR = Path(__file__).parent
STORY_FILE = BASE_DIR / "stories" / "story18.md"

def load_story():
    with open(STORY_FILE, "r", encoding="utf-8") as file:
        return file.read()


def generate_prompt(story):
    return f"""
You are my Turkish tutor in a live voice lesson.
Here is today's turkish story:
---
{story}
---

Run the lesson in three parts, one at a time. Wait for my answer before moving on, and give me brief feedback after each response.

1. Vocabulary quiz: Choose 10 Turkish words from the story. Say each word aloud in english and ask me to say it in Turkish.

2. Sentence translation: Choose 5 sentences from the story. Read each one to me in English and ask me to say it in Turkish.

3. New phrases: Write 5 new English phrases that reuse the vocabulary and grammar patterns from the story. Ask me to say each one in Turkish.
"""


def send_email(prompt):
    sender = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_APP_PASSWORD"]

    message = EmailMessage()
    message["Subject"] = (
        f"Turkish Lesson"
    )
    message["From"] = sender
    message["To"] = sender
    message.set_content(prompt)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(message)


def main():
    story = load_story()

    prompt = generate_prompt(story)

    send_email(prompt)

    print("Email sent successfully!")


if __name__ == "__main__":
    main()