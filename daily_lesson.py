import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


# Files
BASE_DIR = Path(__file__).parent
CURRICULUM_FILE = BASE_DIR / "curriculum.json"

REQUIRED_FIELDS = [
    "level",
    "title",
    "scenario",
    "grammar",
    "vocabulary_theme",
    "briefing",
    "steps",
]

REQUIRED_BRIEFING_FIELDS = [
    "goal",
    "grammar_explanation",
    "examples",
    "key_words",
]


def load_curriculum():
    with open(CURRICULUM_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_curriculum(curriculum):
    # Write atomically to avoid corrupting the curriculum.
    temp_file = CURRICULUM_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(curriculum, file, indent=4, ensure_ascii=False)

    temp_file.replace(CURRICULUM_FILE)


def lesson_number(lesson):
    # Accepts either "lesson" (new format) or "unit" (old format).
    return lesson.get("lesson", lesson.get("unit"))


def progress_key(curriculum):
    # Accepts either "current_lesson" (new) or "current_unit" (old).
    return "current_lesson" if "current_lesson" in curriculum else "current_unit"


def find_lesson(curriculum, number):
    return next(
        (
            lesson
            for lesson in curriculum["lessons"]
            if lesson_number(lesson) == number
        ),
        None,
    )


def validate_lesson(lesson):
    missing = [field for field in REQUIRED_FIELDS if field not in lesson]
    if missing:
        raise ValueError(
            f"Lesson {lesson_number(lesson)} is missing fields: {', '.join(missing)}"
        )

    missing_briefing = [
        field for field in REQUIRED_BRIEFING_FIELDS if field not in lesson["briefing"]
    ]
    if missing_briefing:
        raise ValueError(
            f"Lesson {lesson_number(lesson)} briefing is missing: "
            f"{', '.join(missing_briefing)}"
        )

    steps = lesson["steps"]
    if not steps or all(step.strip() in ("", "...") for step in steps):
        raise ValueError(
            f"Lesson {lesson_number(lesson)} has no real steps yet "
            f"(still a placeholder). Fill them in before sending."
        )


def bullet_lines(items):
    return "\n".join(f"- {item}" for item in items)


def numbered_lines(items):
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1))


def generate_prompt(lesson):
    briefing = lesson["briefing"]

    level = lesson["level"]
    title = lesson["title"]
    scenario = lesson["scenario"]
    grammar = lesson["grammar"]
    vocabulary_theme = lesson["vocabulary_theme"]

    briefing_goal = briefing["goal"]
    grammar_explanation = briefing["grammar_explanation"]
    briefing_examples = bullet_lines(briefing["examples"])
    briefing_key_words = bullet_lines(briefing["key_words"])

    steps = numbered_lines(lesson["steps"])

    return f"""You are my Turkish tutor in a live voice lesson. Run the lesson below
exactly as written. Say only your own lines, and never write my
responses for me.

LESSON
Level: {level}
Title: {title}
Scenario: {scenario}
Grammar focus: {grammar}
Vocabulary theme: {vocabulary_theme}

LESSON FLOW
1. BRIEFING
   Deliver the briefing below in a short, natural way (about one minute).
   Use English for explanations and Turkish for examples and key words.
   Then ask "Ready to practice?" and wait for my answer before moving on.

2. PRACTICE
   Run the practice steps in order, one step per turn. Wait for my reply
   after each one.

3. CLOSE
   After the last step, say "Ders bitti! Tebrikler!" Then give a
   one-sentence English summary of what I practiced. Then stop. Do not
   add extra practice, questions, or new topics.

BRIEFING
Goal: {briefing_goal}
Grammar explanation: {grammar_explanation}
Examples:
{briefing_examples}
Key words:
{briefing_key_words}

PRACTICE STEPS
{steps}

RULES
- Grammar: Use only the grammar focus above. Do not introduce any other
  structures or question forms.
- Vocabulary: Teach and use the key words and the words in the steps.
  Stay within the vocabulary theme. If you need any other new word, give
  its English meaning right away.
- Keep every Turkish sentence short and simple, ideally under 8 words.
- Speak slowly and clearly.
- Say one thing per turn, then wait for me.
- Use English for explanations, corrections, and glossing new words.
  Use Turkish for the actual practice.
- If I make a mistake, give the correct sentence once, have me repeat it,
  then move to the next step. Do not stay on one step more than two tries.
- If I go off-topic or ask about something outside the lesson, answer in
  one short sentence and bring me back to the current step.
- Never skip steps, add steps, or reorder them.

Begin the briefing now.
"""


def send_email(prompt, lesson):
    sender = os.environ["EMAIL_ADDRESS"]
    password = os.environ["EMAIL_APP_PASSWORD"]

    message = EmailMessage()
    message["Subject"] = (
        f"Turkish Lesson {lesson_number(lesson)}: {lesson['title']}"
    )
    message["From"] = sender
    message["To"] = sender
    message.set_content(prompt)

    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(message)


def main():
    curriculum = load_curriculum()

    key = progress_key(curriculum)
    current = curriculum[key]

    lesson = find_lesson(curriculum, current)

    if lesson is None:
        raise ValueError(
            f"Lesson {current} not found in curriculum. "
            f"You may have finished everything!"
        )

    validate_lesson(lesson)

    prompt = generate_prompt(lesson)

    print(f"Sending lesson {current}: {lesson['title']}")

    # Only advance progress if email sending succeeds.
    send_email(prompt, lesson)

    curriculum[key] += 1
    save_curriculum(curriculum)

    print("Email sent successfully!")
    print(f"Next lesson: {curriculum[key]}")


if __name__ == "__main__":
    main()