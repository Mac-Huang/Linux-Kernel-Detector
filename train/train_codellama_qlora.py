# QLoRA fine-tuning for CodeLLaMA-7B-Instruct
# Requirements: transformers, peft, accelerate, bitsandbytes, datasets

from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model
from datasets import load_dataset
import torch
import os

# Paths and parameters
BASE_MODEL = "codellama/CodeLlama-7b-Instruct-hf"
DATA_PATH = "../dataset_builder/output/linux_bugfix_prompt_completion.jsonl"
OUTPUT_DIR = "./output/qlora-codellama-bugfix"

# Load dataset (prompt, completion)
dataset = load_dataset("json", data_files=DATA_PATH, split="train")

# Apply formatting for supervised fine-tuning
def format(example):
    prompt = tokenizer(
        example["prompt"],
        truncation=True,
        padding="max_length",
        max_length=512
    )
    completion = tokenizer(
        example["completion"],
        truncation=True,
        padding="max_length",
        max_length=512
    )
    input_ids = prompt["input_ids"] + completion["input_ids"]
    labels = [-100] * len(prompt["input_ids"]) + completion["input_ids"]

    return {
        "input_ids": input_ids[:1024],
        "labels": labels[:1024]
    }

# Load tokenizer and base model
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, use_fast=True)
tokenizer.pad_token = tokenizer.eos_token  # Required for padding

model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, quantization_config=bnb_config, device_map="auto")

# Apply QLoRA
lora_config = LoraConfig(
    r=64,
    lora_alpha=16,
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# Tokenize dataset
dataset = dataset.map(format, remove_columns=["prompt", "completion"])

# Training args
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    num_train_epochs=3,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    logging_dir=f"{OUTPUT_DIR}/logs",
    logging_steps=10,
    save_strategy="epoch",
    bf16=False,
    fp16=True,
    save_total_limit=2,
    report_to="none",
    push_to_hub=False
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer
)

trainer.train()

model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print(f"[DONE] Model saved to {OUTPUT_DIR}")
