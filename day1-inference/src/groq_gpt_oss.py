import time
from dotenv import load_dotenv
from groq import Groq
import os

# pull GROQ_API_KEY
load_dotenv()

timings = []

t0 = time.time()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
timings.append(("Client init", time.time() - t0))

t0 = time.time()
completion = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
      {
        "role": "user",
        "content": "please give me an aside, written Shakespearean style about a man who just tried to buy a woman a drink and got rejected."
      }
    ],
    temperature=1,
    max_completion_tokens=8192,
    top_p=1,
    reasoning_effort="medium",
    stream=True,
    stop=None
)

first_token_time = None
for chunk in completion:
    if first_token_time is None:
        first_token_time = time.time()
    print(chunk.choices[0].delta.content or "", end="")
stream_done = time.time()

timings.append(("Time to first token", first_token_time - t0 if first_token_time else 0))
timings.append(("Streaming (first to last)", stream_done - first_token_time if first_token_time else 0))
timings.append(("Total API call", stream_done - t0 + timings[0][1]))

# Timing summary
total = timings[-1][1]
col1 = max(len(label) for label, _ in timings)
print("\n\n" + "=" * (col1 + 16))
print(f"{'Step':<{col1}}  {'Time':>8}  {'%':>4}")
print("-" * (col1 + 16))
for label, t in timings:
    pct = (t / total) * 100 if total > 0 else 0
    print(f"{label:<{col1}}  {t:>7.2f}s  {pct:>3.0f}%")
print("=" * (col1 + 16))
