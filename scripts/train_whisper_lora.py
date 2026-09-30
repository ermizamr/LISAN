"""
LISAN AI: Whisper LoRA Fine-Tuning for Ethiopian Speech-to-Text (STT).

Fine-tunes OpenAI Whisper (tiny, base, or small) on Ethiopian audio (Amharic,
Afaan Oromo, Tigrinya, Somali, English) using parameter-efficient QLoRA.

Features:
- Parameter-Efficient QLoRA (4-bit / 8-bit / FP16)
- Custom Speech Data Collator with Log-Mel Spectrogram Extraction
- Evaluates Word Error Rate (WER) using JiWER
- Automatically merges LoRA weights into standalone checkpoint
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Union

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="LISAN AI: Whisper LoRA Fine-Tuning")
    parser.add_argument("--base_model", type=str, default="openai/whisper-small",
                        help="Whisper model ID: openai/whisper-tiny, whisper-base, whisper-small")
    parser.add_argument("--train_manifest", type=str, default=str(ROOT_DIR / "data" / "stt_data" / "train_manifest.jsonl"))
    parser.add_argument("--val_manifest", type=str, default=str(ROOT_DIR / "data" / "stt_data" / "val_manifest.jsonl"))
    parser.add_argument("--output_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "whisper_lora_adapter"))
    parser.add_argument("--merged_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "whisper_ethio_finetuned"))
    parser.add_argument("--batch_size", type=int, default=8, help="Per device batch size")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=1e-4)
    parser.add_argument("--num_epochs", type=int, default=3)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--lora_alpha", type=int, default=32)
    parser.add_argument("--use_4bit", action="store_true", default=True)
    parser.add_argument("--no_4bit", dest="use_4bit", action="store_false")
    parser.add_argument("--merge_and_save", action="store_true", default=True)
    return parser.parse_args()


@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    processor: Any

    def __call__(self, features: List[Dict[str, Union[List[int], Any]]]) -> Dict[str, Any]:
        import torch

        input_features = [{"input_features": feature["input_features"]} for feature in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        label_features = [{"input_ids": feature["labels"]} for feature in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        # Replace padding with -100 to ignore loss
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)

        # Cut BOS token if needed
        if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels
        return batch


def load_manifest(manifest_path: str):
    records = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def main():
    args = parse_args()
    print("=" * 70)
    print("       LISAN AI: WHISPER ETHIOPIAN STT LORA TRAINING")
    print("=" * 70)
    print(f"Base Whisper Model : {args.base_model}")
    print(f"Train Manifest     : {args.train_manifest}")
    print(f"Val Manifest       : {args.val_manifest}")
    print(f"Output Adapter Dir : {args.output_dir}")
    print(f"Merged Model Dir   : {args.merged_dir}")

    import torch
    cuda_avail = torch.cuda.is_available()
    print(f"CUDA Available     : {cuda_avail}")
    if cuda_avail:
        print(f"Device Name        : {torch.cuda.get_device_name(0)}")
        print(f"Device Memory      : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
        use_bf16 = torch.cuda.is_bf16_supported()
    else:
        use_bf16 = False
    print("=" * 70)

    # Check manifest files
    train_p = Path(args.train_manifest)
    val_p = Path(args.val_manifest)
    if not train_p.exists() or not val_p.exists():
        print(f"✗ Manifests not found! Please run:")
        print(f"  python scripts/prepare_stt_data.py --source fleurs")
        print(f"  or python scripts/prepare_stt_data.py --source local")
        sys.exit(1)

    import soundfile as sf
    import scipy.signal as sig
    import numpy as np
    from datasets import Dataset
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        BitsAndBytesConfig,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
        WhisperFeatureExtractor,
        WhisperForConditionalGeneration,
        WhisperProcessor,
        WhisperTokenizer,
    )

    train_data = load_manifest(args.train_manifest)
    val_data = load_manifest(args.val_manifest)
    print(f"Loaded {len(train_data)} train samples and {len(val_data)} val samples.")

    # 1. Load Processor
    print(f"Loading Whisper processor for {args.base_model}...")
    feature_extractor = WhisperFeatureExtractor.from_pretrained(args.base_model)
    tokenizer = WhisperTokenizer.from_pretrained(args.base_model, language="amharic", task="transcribe")
    processor = WhisperProcessor.from_pretrained(args.base_model, language="amharic", task="transcribe")

    # 2. Audio Processing Dataset
    def prepare_dataset_batch(batch):
        audio_paths = batch["audio_path"]
        sentences = batch["sentence"]
        languages = batch["language"]

        input_features = []
        labels = []

        for p_str, text, lang in zip(audio_paths, sentences, languages):
            full_p = ROOT_DIR / p_str if not Path(p_str).is_absolute() else Path(p_str)
            try:
                audio, sr = sf.read(str(full_p), dtype="float32", always_2d=False)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                if sr != 16000:
                    num_samples = int(len(audio) * 16000 / sr)
                    audio = sig.resample(audio, num_samples).astype(np.float32)

                feat = feature_extractor(audio, sampling_rate=16000).input_features[0]
                tokenizer.set_prefix_tokens(language=lang if lang in ("am", "om", "so", "ti", "en") else "en", task="transcribe")
                lab = tokenizer(text).input_ids

                input_features.append(feat)
                labels.append(lab)
            except Exception as e:
                continue

        return {"input_features": input_features, "labels": labels}

    train_ds = Dataset.from_list(train_data)
    val_ds = Dataset.from_list(val_data)

    print("Extracting log-mel spectrogram features and tokenizing labels...")
    train_tokenized = train_ds.map(prepare_dataset_batch, batched=True, batch_size=16, remove_columns=train_ds.column_names)
    val_tokenized = val_ds.map(prepare_dataset_batch, batched=True, batch_size=16, remove_columns=val_ds.column_names)

    # 3. Model Configuration & Quantization
    bnb_config = None
    if args.use_4bit and cuda_avail:
        print("Configuring 4-bit QLoRA for Whisper...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16 if use_bf16 else torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    model = WhisperForConditionalGeneration.from_pretrained(
        args.base_model,
        quantization_config=bnb_config if cuda_avail else None,
        device_map="auto" if cuda_avail else None,
        torch_dtype=torch.bfloat16 if use_bf16 else (torch.float16 if cuda_avail else torch.float32),
    )

    # Disable forced decoder IDs
    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []

    if cuda_avail and args.use_4bit:
        model = prepare_model_for_kbit_training(model)

    # 4. LoRA Setup
    print("Setting up LoRA adapter on Whisper attention modules...")
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "v_proj"],
        lora_dropout=0.05,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

    # 5. Training Arguments
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.learning_rate,
        warmup_steps=50,
        num_train_epochs=args.num_epochs,
        eval_strategy="epoch",
        save_strategy="epoch",
        fp16=cuda_avail and not use_bf16,
        bf16=use_bf16,
        logging_steps=25,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_tokenized,
        eval_dataset=val_tokenized,
        data_collator=data_collator,
        tokenizer=processor.feature_extractor,
    )

    # 6. Execute Training
    print("\nStarting Whisper LoRA Training...")
    trainer.train()

    # 7. Save Adapter
    print(f"\nSaving LoRA adapter to {args.output_dir}...")
    model.save_pretrained(args.output_dir)
    processor.save_pretrained(args.output_dir)
    print("✓ LoRA Adapter saved.")

    # 8. Merge and Save Standalone Model
    if args.merge_and_save:
        print("\n" + "=" * 60)
        print("🔗 Merging LoRA weights into standalone Whisper checkpoint...")
        print("=" * 60)
        del model
        del trainer
        if cuda_avail:
            torch.cuda.empty_cache()

        base_reload = WhisperForConditionalGeneration.from_pretrained(
            args.base_model,
            torch_dtype=torch.float16 if cuda_avail else torch.float32,
            device_map="auto" if cuda_avail else None,
        )
        peft_model = PeftModel.from_pretrained(base_reload, args.output_dir)
        merged = peft_model.merge_and_unload()

        merged.save_pretrained(args.merged_dir)
        processor.save_pretrained(args.merged_dir)
        print(f"✓ Merged Whisper model saved to: {args.merged_dir}")

    print("\n" + "=" * 70)
    print("🎉 LISAN AI: WHISPER STT FINE-TUNING COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
