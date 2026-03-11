"""
Step 4: Side-by-side comparison of base vs fine-tuned model.

Runs test questions through serve.py and prints a markdown table
for use in blog post.

Usage:
    modal run compare.py
"""

import modal

TEST_QUESTIONS = [
    # From training set (should show clear improvement)
    "My CDK deploy is stuck in UPDATE_ROLLBACK_FAILED. How do I fix it?",
    "When should I use EventBridge vs SQS vs SNS?",
    "How do I handle secrets in CDK without hardcoding them?",
    # Novel questions (test generalization)
    "How do I set up a CDK pipeline that deploys to multiple AWS accounts?",
    "What's the best way to add a WAF in front of my API Gateway using CDK?",
    "My Lambda keeps timing out when writing to DynamoDB. What should I check?",
    "How do I structure a CDK project with 20+ stacks?",
]

app = modal.App("lora-compare")
CDKAssistant = modal.Cls.from_name("lora-serve", "CDKAssistant")


@app.local_entrypoint()
def main():
    assistant = CDKAssistant()

    results = []
    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"[{i}/{len(TEST_QUESTIONS)}] {q[:60]}...")
        base = assistant.generate.remote(q, use_adapter=False, max_new_tokens=300)
        tuned = assistant.generate.remote(q, use_adapter=True, max_new_tokens=300)
        results.append({"question": q, "base": base, "tuned": tuned})

    # Print markdown output
    print("\n\n# Base vs Fine-Tuned Comparison\n")
    for r in results:
        print(f"## Q: {r['question']}\n")
        print(f"### Base Model\n{r['base']}\n")
        print(f"### Fine-Tuned\n{r['tuned']}\n")
        print("---\n")
