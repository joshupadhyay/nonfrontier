import time
import modal

app = modal.App("gpt-oss-20b")

# Volume persists model weights across runs — no re-download
model_cache = modal.Volume.from_name("hf-model-cache", create_if_missing=True)
HF_CACHE_DIR = "/root/.cache/huggingface"

# Image only has pip packages — model weights live on the volume
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("transformers", "torch", "accelerate", "kernels")
)

@app.function(
    image=image,
    gpu="A10G",
    timeout=300,
    volumes={HF_CACHE_DIR: model_cache},
)
def generate(prompt: str, max_new_tokens: int = 256) -> dict:
    """Run gpt-oss-20b on a GPU and return output with timings."""
    import torch
    from transformers import pipeline

    timings = []
    logs = []

    logs.append(f"GPU: {torch.cuda.get_device_name(0)}")
    logs.append(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    t0 = time.time()
    pipe = pipeline(
        "text-generation",
        model="openai/gpt-oss-20b",
        torch_dtype="auto",
        device_map="auto",
    )
    timings.append(("Model load", time.time() - t0))
    logs.append(f"Model dtype: {pipe.model.dtype}")
    vram_used = torch.cuda.memory_allocated() / 1e9
    logs.append(f"VRAM used after load: {vram_used:.1f} GB")

    messages = [{"role": "user", "content": prompt}]

    t0 = time.time()
    outputs = pipe(messages, max_new_tokens=max_new_tokens)
    timings.append((f"Inference ({max_new_tokens} max tokens)", time.time() - t0))

    vram_peak = torch.cuda.max_memory_allocated() / 1e9
    logs.append(f"VRAM peak: {vram_peak:.1f} GB")

    # Persist any newly downloaded weights to the volume
    model_cache.commit()

    result = outputs[0]["generated_text"][-1]["content"]

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
