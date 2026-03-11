"""
Step 3: Modal inference endpoint for base + fine-tuned model.

Serves Qwen3-4B with optional LoRA adapter. Toggle `use_adapter` to compare
base vs fine-tuned outputs from a single endpoint.

Usage:
    modal serve serve.py                    # dev mode (hot reload)
    modal deploy serve.py                   # persistent deployment
    modal run serve.py --prompt "How do I..."  # quick test
"""

import re
import modal

app = modal.App("lora-serve")

model_cache = modal.Volume.from_name("hf-model-cache", create_if_missing=True)
lora_data = modal.Volume.from_name("lora-data", create_if_missing=True)

HF_CACHE_DIR = "/root/.cache/huggingface"
DATA_DIR = "/data"

MODEL_ID = "Qwen/Qwen3-4B"

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "torch",
        "transformers",
        "accelerate",
        "peft",
        "bitsandbytes",
    )
)

SYSTEM_PROMPT = """You are a pragmatic AWS/CDK engineer. You are concise and opinionated.
You prefer CDK with TypeScript. You reference specific CLI commands, CDK constructs,
and AWS service details. You give direct answers with concrete examples."""


def strip_think_tags(text: str) -> str:
    """Remove Qwen3 <think>...</think> blocks from output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


@app.cls(
    image=image,
    gpu="A100",  # A100-40GB ~$2/hr, fast inference
    timeout=300,
    volumes={HF_CACHE_DIR: model_cache, DATA_DIR: lora_data},
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
class CDKAssistant:
    adapter_name: str = "v3"

    @modal.enter()
    def load_model(self):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import PeftModel

        print("Loading base model...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        self.base_model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
        )

        # Load LoRA adapter
        adapter_path = f"{DATA_DIR}/adapters/{self.adapter_name}"
        print(f"Loading adapter from {adapter_path}...")
        self.tuned_model = PeftModel.from_pretrained(self.base_model, adapter_path)

        print("Models loaded.")

    @modal.method()
    def generate(self, prompt: str, use_adapter: bool = True, max_new_tokens: int = 512) -> str:
        import torch

        model = self.tuned_model if use_adapter else self.base_model
        if not use_adapter and hasattr(self, "tuned_model"):
            # Disable adapter to get base model behavior
            self.tuned_model.disable_adapter_layers()
            model = self.tuned_model

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )

        # Re-enable adapter if we disabled it
        if not use_adapter and hasattr(self, "tuned_model"):
            self.tuned_model.enable_adapter_layers()

        response = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        return strip_think_tags(response)


@app.local_entrypoint()
def main(prompt: str = "How do I reference resources across stacks in CDK?"):
    assistant = CDKAssistant()

    print("=" * 60)
    print("BASE MODEL:")
    print("-" * 60)
    base_out = assistant.generate.remote(prompt, use_adapter=False)
    print(base_out)

    print("\n" + "=" * 60)
    print("FINE-TUNED:")
    print("-" * 60)
    tuned_out = assistant.generate.remote(prompt, use_adapter=True)
    print(tuned_out)
