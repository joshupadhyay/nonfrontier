import time
import modal

# GPT OSS 20B
MODEL_NAME = "openai/gpt-oss-20b"

# Match the original Part 1 image setup
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("transformers", "torch", "accelerate", "kernels")
)

app = modal.App("hf-baseline-retest")

model_cache = modal.Volume.from_name("hf-model-cache", create_if_missing=True)
HF_CACHE_DIR = "/root/.cache/huggingface"


@app.function(
    image=image,
    gpu="A10G",
    timeout=600,
    volumes={HF_CACHE_DIR: model_cache},
)
def generate(prompt: str, max_new_tokens: int = 256) -> dict:
    """Run gpt-oss-20b on a GPU via HF transformers with fixed token output."""
    import torch
    from transformers import pipeline

    timings = []
    logs = []

    logs.append(f"GPU: {torch.cuda.get_device_name(0)}")
    logs.append(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    t0 = time.time()
    pipe = pipeline(
        "text-generation",
        model=MODEL_NAME,
        torch_dtype="auto",
        device_map="auto",
    )
    timings.append(("Model load", time.time() - t0))
    logs.append(f"Model dtype: {pipe.model.dtype}")

    vram_used = torch.cuda.memory_allocated() / 1e9
    logs.append(f"VRAM used after load: {vram_used:.1f} GB")

    messages = [{"role": "user", "content": prompt}]

    t0 = time.time()
    outputs = pipe(
        messages,
        max_new_tokens=max_new_tokens,
        min_new_tokens=max_new_tokens,  # force exactly 256 tokens
    )
    timings.append((f"Inference ({max_new_tokens} fixed tokens)", time.time() - t0))

    vram_peak = torch.cuda.max_memory_allocated() / 1e9
    logs.append(f"VRAM peak: {vram_peak:.1f} GB")

    model_cache.commit()

    result = outputs[0]["generated_text"][-1]["content"]

    # Count actual output tokens
    token_count = len(pipe.tokenizer.encode(result))
    logs.append(f"Output tokens: {token_count}")

    return {"result": result, "timings": timings, "logs": logs}


@app.local_entrypoint()
def main():
    prompt = "please give me an aside, written Shakespearean style about a man who just tried to buy a woman a drink and got rejected."

    t0 = time.time()
    output = generate.remote(prompt, max_new_tokens=256)
    total_remote = time.time() - t0

    print(output["result"])

    # GPU logs
    print("\n" + "=" * 45)
    print("GPU INFO")
    print("-" * 45)
    for log in output["logs"]:
        print(f"  {log}")

    # Timing summary
    timings = output["timings"]
    timings.append(("Total (including Modal overhead)", total_remote))

    col1 = max(len(label) for label, _ in timings)
    print("\n" + "=" * (col1 + 16))
    print(f"{'Step':<{col1}}  {'Time':>8}  {'%':>4}")
    print("-" * (col1 + 16))
    for label, t in timings:
        pct = (t / total_remote) * 100 if total_remote > 0 else 0
        print(f"{label:<{col1}}  {t:>7.2f}s  {pct:>3.0f}%")
    print("=" * (col1 + 16))
