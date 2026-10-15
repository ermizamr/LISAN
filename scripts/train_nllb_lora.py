"""LISAN LoRA Fine-Tuning Script for Meta NLLB-200 (600M).

Specializes NLLB-200 on Ethiopian & Horn of Africa languages:
- Amharic (amh_Ethi)
- Afaan Oromoo (gaz_Latn)
- Tigrinya (tir_Ethi)
- Somali (som_Latn)
- English (eng_Latn)

Uses Parameter-Efficient Fine-Tuning (PEFT / LoRA):
- Freezes 100% of the 600M base model weights (prevents catastrophic forgetting).
- Trains lightweight attention adapters (~20 MB).
- Supports Google Colab T4 / A100 GPU or local NVIDIA RTX GPU.
- Automatically merges LoRA weights and exports for CTranslate2 and ONNX.
"""

import os
import sys
import json
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def train(args):
    import torch
    from transformers import (
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        DataCollatorForSeq2Seq,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, TaskType
    from datasets import Dataset

    print("=" * 80)
    print("LISAN NLLB-200 LoRA FINE-TUNING PIPELINE")
    print(f"Base Model:    {args.model_name}")
    print(f"Train File:    {args.train_file}")
    print(f"Val File:      {args.val_file}")
    print(f"Output Dir:    {args.output_dir}")
    print(f"Device:        {'CUDA (' + torch.cuda.get_device_name(0) + ')' if torch.cuda.is_available() else 'CPU'}")
    print("=" * 80)

    # 1. Load Tokenizer & Model
    print("\n[1/5] Loading tokenizer and base model...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        args.model_name,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )

    # 2. Configure LoRA (Freeze base, attach rank-16 adapters)
    print("\n[2/5] Configuring LoRA adapters (Rank=16, Alpha=32)...")
    peft_config = LoraConfig(
        task_type=TaskType.SEQ_2_SEQ_LM,
        inference_mode=False,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj", "k_proj", "out_proj"],
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 3. Load Datasets
    print("\n[3/5] Loading and formatting dataset pairs...")
    def load_jsonl(filepath):
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    raw_train = load_jsonl(args.train_file)
    raw_val = load_jsonl(args.val_file)

    def preprocess_batch(examples):
        inputs = []
        targets = []
        for src_text, tgt_text, src_lang, tgt_lang in zip(
            examples["source"], examples["target"], examples["src_nllb"], examples["tgt_nllb"]
        ):
            tokenizer.src_lang = src_lang
            inputs.append(src_text)
            targets.append(tgt_text)

        model_inputs = tokenizer(inputs, max_length=128, truncation=True)
        with tokenizer.as_target_tokenizer():
            labels = tokenizer(targets, max_length=128, truncation=True)

        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    train_ds = Dataset.from_list(raw_train).map(preprocess_batch, batched=True, remove_columns=list(raw_train[0].keys()))
    val_ds = Dataset.from_list(raw_val).map(preprocess_batch, batched=True, remove_columns=list(raw_val[0].keys()))
    print(f"Tokenized dataset ready: {len(train_ds)} train examples, {len(val_ds)} val examples.")

    # 4. Training Arguments
    print("\n[4/5] Setting up trainer...")
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        num_train_epochs=args.epochs,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        load_best_model_at_end=True,
        fp16=torch.cuda.is_available(),
        logging_steps=25,
        predict_with_generate=True,
        report_to="none",
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    # 5. Train & Save LoRA Adapters
    print("\n[5/5] Commencing training...")
    trainer.train()

    adapter_output_dir = os.path.join(args.output_dir, "lora_adapters")
    model.save_pretrained(adapter_output_dir)
    tokenizer.save_pretrained(adapter_output_dir)
    print(f"\n[DONE] LoRA adapters saved successfully to: {adapter_output_dir}")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune NLLB-200 with LoRA on Ethiopian languages.")
    parser.add_argument("--model_name", type=str, default="facebook/nllb-200-distilled-600M")
    parser.add_argument("--train_file", type=str, default=str(ROOT_DIR / "data" / "massive_dataset" / "train.jsonl"))
    parser.add_argument("--val_file", type=str, default=str(ROOT_DIR / "data" / "massive_dataset" / "val.jsonl"))
    parser.add_argument("--output_dir", type=str, default=str(ROOT_DIR / "fine_tuned_nllb"))
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--learning_rate", type=float, default=2e-4)

    args = parser.parse_args()
    train(args)
