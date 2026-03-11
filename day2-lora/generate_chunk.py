"""Helper: generate a single chunk of training data. Called by parallel agents."""
import json, re, sys
from anthropic import Anthropic

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

chunk_num = sys.argv[1]
questions = sys.argv[2:]

client = Anthropic()
results = []
for q in questions:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=4096,
        messages=[{"role": "user", "content": GENERATION_PROMPT.format(question=q)}],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    variations = json.loads(text)
    for var in variations:
        results.append(json.dumps({"messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": var["question"]},
            {"role": "assistant", "content": var["answer"]},
        ]}))

outpath = f"data/chunk_{chunk_num}.jsonl"
with open(outpath, "w") as f:
    f.write("\n".join(results) + "\n")
print(f"Wrote {len(results)} examples to {outpath}")
