"""
Step 1: Generate synthetic training data from seed questions.

Parses QUESTIONS.md, calls Claude to generate 5 Q&A variations per seed question,
outputs data/training_data.jsonl in chat format for SFTTrainer.

Usage:
    uv run python generate_data.py
"""

import json
import re
from pathlib import Path

import anthropic

QUESTIONS_FILE = Path(__file__).parent / "QUESTIONS.md"
OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "training_data.jsonl"

SYSTEM_PROMPT = """You are a pragmatic AWS/CDK engineer. You are concise and opinionated.
You prefer CDK with TypeScript. You reference specific CLI commands, CDK constructs,
and AWS service details. You give direct answers with concrete examples."""

GENERATION_PROMPT = """Given this AWS/CDK question, generate exactly 5 varied Q&A pairs.

Each variation should:
- Rephrase the question differently (different wording, angle, or specificity level)
- Provide a helpful, concise answer in the voice of a pragmatic AWS/CDK engineer
- Include specific CDK constructs, CLI commands, or AWS service details where relevant
- Be self-contained (the answer shouldn't reference the other variations)

Original question: {question}

Respond with a JSON array of exactly 5 objects, each with "question" and "answer" fields.
Return ONLY the JSON array, no other text."""


def parse_questions(path: Path) -> list[str]:
    """Extract numbered questions from QUESTIONS.md."""
    text = path.read_text()
    questions = re.findall(r"^\d+\.\s+(.+)$", text, re.MULTILINE)
    return questions


def generate_variations(client: anthropic.Anthropic, question: str) -> list[dict]:
    """Call Claude to generate 5 Q&A variations for a seed question."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": GENERATION_PROMPT.format(question=question),
            }
        ],
    )

    text = response.content[0].text.strip()
    # Handle markdown code blocks
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    return json.loads(text)


def to_chat_format(question: str, answer: str) -> dict:
    """Convert Q&A pair to chat message format for SFTTrainer."""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    }


def main():
    questions = parse_questions(QUESTIONS_FILE)
    print(f"Parsed {len(questions)} seed questions from QUESTIONS.md")

    client = anthropic.Anthropic()
    OUTPUT_DIR.mkdir(exist_ok=True)

    total = 0
    with open(OUTPUT_FILE, "w") as f:
        for i, q in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] {q[:80]}...")
            try:
                variations = generate_variations(client, q)
                for var in variations:
                    example = to_chat_format(var["question"], var["answer"])
                    f.write(json.dumps(example) + "\n")
                    total += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                continue

    print(f"\nGenerated {total} training examples → {OUTPUT_FILE}")
    print(f"\nNext: upload to Modal volume:")
    print(f"  modal volume put lora-data {OUTPUT_FILE} training/training_data.jsonl")


if __name__ == "__main__":
    main()
