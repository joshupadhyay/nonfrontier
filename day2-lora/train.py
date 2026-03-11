"""
Step 2: QLoRA fine-tuning of Qwen3-4B on Modal GPU.

Loads training data from Modal volume, fine-tunes with PEFT + TRL SFTTrainer,
saves LoRA adapter weights back to the volume.

Usage:
    modal run train.py --run-name v1
"""

import modal

app = modal.App("lora-finetune")

# Volumes
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
        "trl",
        "bitsandbytes",
        "datasets",
    )
)


@app.function(
    image=image,
    gpu="A100",  # A100-40GB ~$2/hr, fast training
    timeout=3600,
    volumes={HF_CACHE_DIR: model_cache, DATA_DIR: lora_data},
    secrets=[modal.Secret.from_name("huggingface-secret")],
)
def train(run_name: str = "v1"):
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )
    from trl import SFTConfig, SFTTrainer

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

    # --- Tokenizer ---
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.model_max_length = 1024

    # --- QLoRA: 4-bit quantization ---
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model_cache.commit()

    model = prepare_model_for_kbit_training(model)

    vram_used = torch.cuda.memory_allocated() / 1e9
    print(f"VRAM after model load: {vram_used:.1f} GB")

    # --- LoRA config ---
    lora_config = LoraConfig(
        r=32,
        lora_alpha=64,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # --- Dataset ---
    data_path = f"{DATA_DIR}/training/training_data.jsonl"
    dataset = load_dataset("json", data_files=data_path, split="train")
    print(f"Training examples: {len(dataset)}")

    # --- Training ---
    output_dir = f"/tmp/lora-output-{run_name}"
    adapter_save_path = f"{DATA_DIR}/adapters/{run_name}"

    training_args = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=4,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,
        bf16=True,
        logging_steps=5,
        save_strategy="no",
        warmup_steps=10,
        lr_scheduler_type="cosine",
        dataset_text_field=None,
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        processing_class=tokenizer,
    )

    print("Starting training...")
    result = trainer.train()

    print(f"\nTraining complete!")
    print(f"  Loss: {result.training_loss:.4f}")
    print(f"  Runtime: {result.metrics['train_runtime']:.0f}s")
    print(f"  Samples/sec: {result.metrics['train_samples_per_second']:.1f}")

    # Save adapter
    model.save_pretrained(adapter_save_path)
    tokenizer.save_pretrained(adapter_save_path)
    lora_data.commit()
    print(f"Adapter saved to volume at {adapter_save_path}")

    return {
        "run_name": run_name,
        "loss": result.training_loss,
        "runtime_s": result.metrics["train_runtime"],
        "adapter_path": adapter_save_path,
    }


@app.local_entrypoint()
def main(run_name: str = "v1"):
    result = train.remote(run_name)
    print("\n" + "=" * 40)
    for k, v in result.items():
        print(f"  {k}: {v}")
