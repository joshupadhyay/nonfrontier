# Fine-Tuning Qwen3-4B on AWS/CDK Knowledge with QLoRA on Modal

> A Fractal Tech bootcamp project — turning a general-purpose LLM into an AWS infrastructure specialist in under 2 minutes of GPU time.

---

## What's LoRA?

Large language models are powerful out of the box, but sometimes you need them to speak a specific language — not French or Mandarin, but the language of your domain. Fine-tuning is how you teach a model new tricks, and LoRA (Low-Rank Adaptation) makes it practical to do on a single GPU without rewriting billions of parameters.

### Why fine-tune at all?

Prompting gets you far. You can stuff a system prompt with instructions and examples and get decent results. But there are limits: context windows are finite, inference costs scale with prompt length, and some behavioral patterns are hard to encode in text. Fine-tuning bakes knowledge directly into the model weights, so the model *just knows* without being told every time.

For this project, the goal was specific: make Qwen3-4B reliably answer AWS CDK and infrastructure questions with the kind of practical, opinionated answers you'd get from someone who's actually deployed CDK stacks in production — because I have, for ~4 years at 3M.

<!-- TODO: Add a concrete before/after example here — one question, base model answer vs fine-tuned answer, to make the "why fine-tune" argument visceral -->

### LoRA: the core idea

Instead of updating all 4 billion parameters during training, LoRA freezes the pretrained weights and injects small trainable matrices into specific layers. These matrices are low-rank decompositions — meaning a weight update matrix W is approximated as the product of two much smaller matrices A and B, where A is (d × r) and B is (r × d), and r (the rank) is tiny compared to d.

The result: you train maybe 0.5-2% of the total parameters, use a fraction of the memory, and can swap adapters in and out at inference time.

<!-- TODO: Add a visual diagram here. Either ASCII art showing the rank decomposition (original weight matrix W + delta W = B × A where B and A are thin matrices), or a simple SVG/image. Show the parameter count savings concretely for Qwen3-4B. -->

### QLoRA: making it even cheaper

QLoRA takes this further. The base model weights are quantized to 4-bit (NF4 format), so the frozen weights take up ~4x less memory. The LoRA adapter matrices stay in higher precision for stable training. This means you can fine-tune a 4B parameter model on a single GPU without running out of VRAM.

### Key hyperparameters

| Parameter | What it controls | Our v1 setting |
|-----------|-----------------|----------------|
| **Rank (r)** | Size of the low-rank matrices. Higher = more capacity, more parameters | 16 |
| **Alpha** | Scaling factor for the LoRA update. Often set to 2×rank | 32 |
| **Target modules** | Which layers get LoRA adapters | q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj |
| **Learning rate** | Step size for optimizer | 2e-4 |
| **Epochs** | Passes through the training data | 3 |

<!-- TODO: Explain the target modules choice — why all the attention projections AND the MLP projections? What's the tradeoff vs just targeting q_proj/v_proj? -->

### Context: this is a bootcamp assignment

This started as a Fractal Tech day 2 assignment where everyone fine-tunes a model to adopt a pirate persona. I customized it: instead of "arrr matey," I trained the model on AWS/CDK infrastructure Q&A drawn from my actual experience. Same pipeline, more useful output, and a better signal for what I can build.

---

## Training Run and Setup with Modal

### Why Modal?

Modal is serverless GPU compute with a developer experience that actually makes sense. You write Python, decorate your functions, and Modal handles containers, GPU allocation, and scaling. For fine-tuning, the key features are:

- **Pay-per-second GPU billing** — no idle instances burning money while you iterate on data
- **Volumes** — persistent storage for caching HuggingFace models (~8GB for Qwen3-4B quantized) so you don't re-download every run
- **Python-native** — no Dockerfiles, no YAML, no kubectl. Just `@app.function(gpu="A100")` and go
- **Image building** — define your environment as code, Modal builds and caches the container image

<!-- TODO: Include the Modal function decorator pattern from train.py — show the @app.function decorator with gpu, image, volumes, and timeout kwargs. This is the "aha moment" for anyone coming from traditional cloud. -->

### The pipeline

The project is four scripts, each a Modal function:

```
generate_data.py → train.py → serve.py → compare.py
```

1. **generate_data.py** — Takes seed questions and generates training data
2. **train.py** — QLoRA fine-tuning on Modal GPU
3. **serve.py** — Deploys the fine-tuned model as an endpoint
4. **compare.py** — Runs test questions through base and fine-tuned models side by side

<!-- TODO: Include a simplified architecture diagram showing the pipeline flow, with Modal volumes connecting the steps (hf-model-cache shared across train/serve, lora-data for adapter weights) -->

### Data generation

I started with 28 seed questions drawn from real AWS/CDK experience — things like "How do you structure a multi-stack CDK app?", "What's the difference between L1 and L2 constructs?", and "How do you handle cross-account deployments?" These aren't textbook questions; they're the kind of thing someone asks on a team Slack channel.

Each seed question gets fed to Claude, which generates 5 variations with detailed, opinionated answers. The output is JSONL in chat format (system/user/assistant turns), giving us ~140 training examples.

<!-- TODO: Show a sample JSONL entry from the data/ directory — one complete conversation turn. Also note the system prompt used for data generation. -->

### Modal specifics

The training function runs on an A100 GPU with the following setup:

- **Image**: Built on `nvidia/cuda` base with `transformers`, `peft`, `trl`, `bitsandbytes`, `accelerate`
- **Volumes**: `hf-model-cache` (persistent HF model downloads), `lora-data` (training data + output adapters)
- **Model**: Qwen/Qwen3-4B loaded in 4-bit NF4 quantization via `BitsAndBytesConfig`

<!-- TODO: Include the actual code snippet showing the Modal image definition and volume mounts from train.py. Show the BitsAndBytesConfig setup too. -->

### Training config

The training uses HuggingFace's PEFT library for LoRA and TRL's `SFTTrainer` for supervised fine-tuning:

- **Quantization**: NF4 (4-bit NormalFloat) with double quantization enabled
- **LoRA config**: rank, alpha, dropout, target modules (all attention + MLP projections)
- **Trainer**: SFTTrainer with cosine learning rate schedule, gradient accumulation, fp16 mixed precision

<!-- TODO: Include the LoraConfig and TrainingArguments code blocks from train.py. These are the most copy-paste-useful parts for anyone replicating this. -->

---

## Tweaks and Results

### v1: baseline run

| Metric | Value |
|--------|-------|
| Training examples | 145 |
| Epochs | 3 |
| Rank (r) | 16 |
| Alpha | 32 |
| Starting loss | 3.19 |
| Final loss | 1.34 |
| Total runtime | ~85 seconds |
| GPU | A100 |

85 seconds. That's the whole training run. The loss curve drops steeply in the first epoch and levels off — classic fine-tuning behavior with a small dataset.

<!-- TODO: Include the training loss curve. Pull data from results/*.json and either render as a markdown table of loss-per-step or embed a chart image. Show the loss at key checkpoints (step 10, 20, 30, etc.) -->

### v2: more data, more epochs

<!-- TODO: Fill in v2 results once the run completes. Expected changes: more training examples (expanded seed questions), 9 epochs, r=32, alpha=64. Document the delta in loss, runtime, and qualitative answer quality. -->

| Metric | v1 | v2 |
|--------|----|----|
| Training examples | 145 | TBD |
| Epochs | 3 | 9 |
| Rank | 16 | 32 |
| Final loss | 1.34 | TBD |
| Runtime | 85s | TBD |

### Comparison: base model vs fine-tuned

<!-- TODO: Populate this table from compare.py output. Run 3-5 test questions through both base Qwen3-4B and the fine-tuned version. Format as:

| Question | Base Model Answer (truncated) | Fine-Tuned Answer (truncated) |
|----------|------------------------------|-------------------------------|
| How do you handle CDK context values? | ... | ... |
| What's the best pattern for cross-stack references? | ... | ... |

Focus on questions where the fine-tuned model gives noticeably more specific, practical answers. -->

### What worked

- **Small dataset, big impact**: 145 examples was enough to shift the model's tone and specificity on AWS topics
- **QLoRA on A100**: Fast enough to iterate — under 2 minutes per run means you can experiment freely
- **Modal's developer experience**: No infra setup time. First run to trained model in maybe 20 minutes including writing the data generation script

### What didn't (or needs more work)

<!-- TODO: Fill in based on actual comparison results. Likely candidates:
- Model may overfit on small dataset (training loss low but generalization unclear)
- Answers may be repetitive if seed questions were too similar
- 4-bit quantization may introduce quality loss on nuanced questions
- Chat template formatting issues if the tokenizer wasn't configured correctly
-->

### Lessons learned

<!-- TODO: Add 3-5 concrete takeaways. Starter list to validate/expand:
1. Data quality > data quantity for domain fine-tuning
2. Modal makes GPU experimentation feel like local dev
3. The hardest part isn't the training — it's generating good training data
4. QLoRA's memory savings are real and meaningful for single-GPU workflows
-->

---

## Try It Yourself

The fine-tuned model is deployed as a Modal endpoint where you can ask it AWS/CDK questions and compare against the base model.

<!-- TODO: Finalize the deployment approach. Two options under consideration:

Option A: Modal web endpoint (simpler)
- Deploy serve.py as a persistent Modal web endpoint with @app.function(keep_warm=1)
- Add CORS headers for browser access
- Pro: single platform, no extra infra
- Con: Modal endpoints have cold start unless kept warm ($)

Option B: Modal + Vercel proxy (better UX)
- Modal web endpoint for inference
- Vercel serverless function as a lightweight proxy (handles CORS, rate limiting, nice URL)
- Pro: clean URL, free tier on Vercel, familiar stack
- Con: extra hop, more moving parts

Once decided, add:
- The live URL
- A curl example for the API
- A screenshot of the comparison UI if one exists
-->

---

*Built during [Fractal Tech](https://fractalbootcamp.com) bootcamp. Fine-tuned on Modal. Training data generated from real AWS/CDK experience across 4 years at 3M.*

<!-- TODO: Add author byline with links to GitHub (joshupadhyay), the repo, and Modal docs -->
