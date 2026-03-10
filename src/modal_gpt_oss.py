import time
import modal

# GPT OSS 20B
MODEL_NAME = "openai/gpt-oss-20b"

# Define the container image with vLLM and dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "vllm>=0.8",
        "transformers<5",  # vLLM 0.8 is incompatible with transformers 5 (TokenizersBackend missing all_special_tokens_extended)
        "huggingface_hub[hf_transfer]",
        "flashinfer-python",
    )
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "HF_HOME": "/models",  # align HF cache with Modal volume so weights persist across cold starts
    })
)

app = modal.App(MODEL_NAME)

# Persistent volumes to cache model weights and vLLM compile artifacts across cold starts
volume = modal.Volume.from_name("model-cache", create_if_missing=True)

# persist vLLM cache to save torch.compile output, and CUDA graph captures
# claude estimates this will save ~50s (24 sec torch.compile, 19 sec CUDA graph captures)
compile_cache = modal.Volume.from_name("vllm-compile-cache", create_if_missing=True)


@app.function(
    image=image,
    gpu="A10G",
    timeout=300,
    volumes={"/models": volume, "/root/.cache/vllm": compile_cache},
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
def generate(prompt: str, max_new_tokens: int = 256) -> dict:
    """Run gpt-oss-20b on a GPU via vLLM and return output with timings."""
    import torch
    ## we import vllm here. These are imports for Modal's container, so it's nested under this function
    ## vLLM uses CUDA / other deps that my Macbook does not have, but runs in Modal just fine. 
    from vllm import LLM, SamplingParams

    timings = []
    logs = []

    logs.append(f"GPU: {torch.cuda.get_device_name(0)}")
    logs.append(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    t0 = time.time()
    llm = LLM(model=MODEL_NAME, download_dir="/models")
    timings.append(("Model load", time.time() - t0))

    vram_used = torch.cuda.memory_allocated() / 1e9
    logs.append(f"VRAM used after load: {vram_used:.1f} GB")

    t0 = time.time()
    params = SamplingParams(max_tokens=max_new_tokens, min_tokens=max_new_tokens)
    outputs = llm.generate([prompt], params)
    timings.append((f"Inference ({max_new_tokens} fixed tokens)", time.time() - t0))

    vram_peak = torch.cuda.max_memory_allocated() / 1e9
    logs.append(f"VRAM peak: {vram_peak:.1f} GB")

    volume.commit()

    result = outputs[0].outputs[0].text
    token_count = len(outputs[0].outputs[0].token_ids)
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
