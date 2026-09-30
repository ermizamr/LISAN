"""
Fine-Tune NLLB-200-distilled-600M with LoRA (Low-Rank Adaptation) on Ethiopian Multilingual Corpus.

Languages:
- Afaan Oromoo (gaz_Latn)
- Amharic (amh_Ethi)
- Tigrinya (tir_Ethi)
- Somali (som_Latn)
- English (eng_Latn)

Designed to run on AWS GPU instances (g4dn.xlarge with NVIDIA T4 16GB or g5.xlarge with A10G 24GB).
Supports 4-bit QLoRA to drastically reduce VRAM footprint while preserving full parameter quality.
"""

import argparse
import json
import os
import sys
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)


def parse_args():
    parser = argparse.ArgumentParser(description="LoRA Fine-Tuning for NLLB-200 on Ethiopian Languages")
    parser.add_argument("--base_model", type=str, default="facebook/nllb-200-distilled-600M")
    parser.add_argument("--train_file", type=str, default="data/training_data/train.jsonl")
    parser.add_argument("--val_file", type=str, default="data/training_data/val.jsonl")
    parser.add_argument("--output_dir", type=str, default="./lisan_nllb_lora_weights")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--grad_accum", type=int, default=2)
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--num_epochs", type=int, default=3)
    parser.add_argument("--max_length", type=int, default=128)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--use_4bit", action="store_true", default=True)
    return parser.parse_args()


def main():
    args = parse_args()
    print("=" * 60)
    print("LISAN AI: NLLB-200 ETHIOPIAN MULTILINGUAL LORA TRAINING")
    print("=" * 60)
    print(f"Base Model    : {args.base_model}")
    print(f"Train File    : {args.train_file}")
    print(f"Val File      : {args.val_file}")
    print(f"Output Dir    : {args.output_dir}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device Name   : {torch.cuda.get_device_name(0)}")
        print(f"Device Memory : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
    print("=" * 60)

    # 1. Load Tokenizer
    print("Loading NLLB tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)

    # 2. Load Dataset
    print(f"Loading datasets from {args.train_file} and {args.val_file}...")
    dataset = load_dataset(
        "json",
        data_files={"train": args.train_file, "val": args.val_file},
    )
    print(f"Train samples: {len(dataset['train'])}, Validation samples: {len(dataset['val'])}")

    # 3. Preprocessing function (strictly enforces NLLB source and target language tokens)
    def preprocess_function(examples):
        inputs = examples["source"]
        targets = examples["target"]
        src_langs = examples["src_nllb"]
        tgt_langs = examples["tgt_nllb"]

        model_inputs = {"input_ids": [], "attention_mask": [], "labels": []}

        for inp, tgt, src_l, tgt_l in zip(inputs, targets, src_langs, tgt_langs):
            tokenizer.src_lang = src_l
            tokenizer.tgt_lang = tgt_l
            tok = tokenizer(
                text=inp,
                text_target=tgt,
                max_length=args.max_length,
                truncation=True,
            )
            model_inputs["input_ids"].append(tok["input_ids"])
            model_inputs["attention_mask"].append(tok["attention_mask"])
            model_inputs["labels"].append(tok["labels"])

        return model_inputs

    print("Tokenizing datasets...")
    tokenized_datasets = dataset.map(
        preprocess_function,
        batched=True,
        batch_size=1000,
        remove_columns=dataset["train"].column_names,
    )

    # 4. Quantization Configuration (4-bit QLoRA)
    bnb_config = None
    if args.use_4bit and torch.cuda.is_available():
        print("Configuring 4-bit Quantization (QLoRA)...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    # 5. Load Base Model
    print(f"Loading {args.base_model}...")
    model = AutoModelForSeq2SeqLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config if torch.cuda.is_available() else None,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    if torch.cuda.is_available() and args.use_4bit:
        model = prepare_model_for_kbit_training(model)

    # 6. LoRA Configuration
    print("Setting up LoRA PEFT adapters...")
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=["q_proj", "v_proj", "k_proj", "out_proj"],
        bias="none",
        task_type=TaskType.SEQ_2_SEQ_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 7. Data Collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        label_pad_token_id=-100,
    )

    # 8. Training Arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        weight_decay=0.01,
        save_total_limit=2,
        num_train_epochs=args.num_epochs,
        predict_with_generate=False,
        fp16=torch.cuda.is_available(),
        logging_steps=50,
        warmup_ratio=0.05,
        report_to="none",
    )

    # 9. Trainer
    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets["train"],
        eval_dataset=tokenized_datasets["val"],
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    # 10. Execute Training
    print("\nStarting LoRA Fine-Tuning...")
    trainer.train()

    # 11. Save Adapter & Tokenizer
    print(f"\nSaving fine-tuned LoRA adapter to {args.output_dir}...")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("✓ LoRA Training Completed and Adapter Weights Saved Successfully!")


if __name__ == "__main__":
    main()
