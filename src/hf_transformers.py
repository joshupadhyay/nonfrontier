import time
from dotenv import load_dotenv
from transformers import pipeline
from sentence_transformers import SentenceTransformer

# load HF_TOKEN
load_dotenv()

timings = []

# High-level pipeline API

## without any information, HF will default to a small model
t0 = time.time()
classifier = pipeline("text-generation")
timings.append(("Classifier load", time.time() - t0))

t0 = time.time()
result = classifier("I love open source models!")
timings.append(("Classifier inference", time.time() - t0))

# Text generation
t0 = time.time()
generator = pipeline(
    "text-generation",
    model="distilgpt2", # since this is running the model locally, need something more performant! :)
    device_map="auto"  # auto GPU placement, requires 'accelerate' pkg
)
timings.append(("Generator load (distilgpt2)", time.time() - t0))

t0 = time.time()
output = generator("please give me an aside, written Shakespearean style about a man who just tried to buy a woman a drink and got rejected.", max_new_tokens=100)
timings.append(("Generator inference (100 tokens)", time.time() - t0))

# Text generation, with a larger model 
t0 = time.time()
generator = pipeline(
    "text-generation",
    device_map="auto"  # auto GPU placement, requires 'accelerate' pkg,
)
output = generator("please give me an aside, written Shakespearean style about a man who just tried to buy a woman a drink and got rejected.", max_new_tokens=100)

timings.append(("Generator load (HF smol)", time.time() - t0))


print(output)

# Timing summary
total = sum(t for _, t in timings)
col1 = max(len(label) for label, _ in timings)
print("\n" + "=" * (col1 + 16))
print(f"{'Step':<{col1}}  {'Time':>8}  {'%':>4}")
print("-" * (col1 + 16))
for label, t in timings:
    pct = (t / total) * 100 if total > 0 else 0
    print(f"{label:<{col1}}  {t:>7.2f}s  {pct:>3.0f}%")
print("-" * (col1 + 16))
print(f"{'TOTAL':<{col1}}  {total:>7.2f}s")
print("=" * (col1 + 16))


# model = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5")
# embeddings = model.encode(["Hello world", "Open source AI"])