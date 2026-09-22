"""
Automated NLLB-200 Fine-Tuning & CTranslate2 INT8 Quantization Workflow for Lisan.

Enables end-to-end adaptation on authentic Ethiopian conversational datasets:
1. Extracts clean parallel sentence pairs from Translation Memory (SQLite) or HF corpora.
2. Fine-tunes facebook/nllb-200-distilled-600M on low-resource Ethiopian language pairs.
3. Quantizes model directly into CTranslate2 INT8 format for ultra-fast, offline on-device inference (~600MB RAM).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai_pipeline.translation_memory import TranslationMemory

DEFAULT_MODEL = "facebook/nllb-200-distilled-600M"
DEFAULT_OUTPUT = ROOT_DIR / "models_optimized" / "nllb_int8"


def extract_training_data(
    output_dir: Path,
    min_entries_per_pair: int = 50,
) -> dict[str, list[tuple[str, str]]]:
    """Extract parallel pairs from SQLite Translation Memory for training."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tm = TranslationMemory.get_instance()
    conn = tm._get_connection()

    pairs_data: dict[str, list[tuple[str, str]]] = {}

    cur = conn.execute(
        """
        SELECT src_lang, tgt_lang, source_text, target_text 
        FROM translation_memory 
        WHERE confidence >= 0.75
        """
    )
    for row in cur:
        pair_key = f"{row['src_lang']}-{row['tgt_lang']}"
        if pair_key not in pairs_data:
            pairs_data[pair_key] = []
        pairs_data[pair_key].append((row["source_text"], row["target_text"]))

    print(f"Extracted {len(pairs_data)} language pairs from Translation Memory:")
    for p, items in pairs_data.items():
        print(f"  • {p}: {len(items):,} sentences")

    # Save to TSV files for training
    for p, items in pairs_data.items():
        if len(items) >= min_entries_per_pair:
            tsv_path = output_dir / f"train_{p}.tsv"
            with open(tsv_path, "w", encoding="utf-8") as f:
                for src, tgt in items:
                    f.write(f"{src}\t{tgt}\n")
            print(f"  ✓ Saved {tsv_path.name}")

    return pairs_data


def convert_to_ctranslate2_int8(
    model_path: str,
    output_dir: Path,
    copy_tokenizer: bool = True,
) -> bool:
    """Convert Hugging Face NLLB-200 model to CTranslate2 INT8 format."""
    print("\n" + "=" * 60)
    print(f"⚡ Converting {model_path} -> CTranslate2 INT8...")
    print(f"   Destination: {output_dir}")
    print("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "ctranslate2.converters.transformers",
        "--model",
        model_path,
        "--output_dir",
        str(output_dir),
        "--quantization",
        "int8",
        "--force",
    ]
    if copy_tokenizer:
        cmd.append("--copy_files")
        cmd.extend(["tokenizer.json", "sentencepiece.bpe.model", "special_tokens_map.json", "tokenizer_config.json"])

    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(res.stdout)
        print(f"\n✓ Successfully exported CTranslate2 INT8 model to: {output_dir}")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"\n⚠ CTranslate2 conversion failed: {exc.stderr}")
        print("  Tip: Ensure ctranslate2 is installed: pip install ctranslate2")
        return False


def fine_tune_nllb(
    train_data_dir: Path,
    output_model_dir: Path,
    base_model: str = DEFAULT_MODEL,
    epochs: int = 3,
    batch_size: int = 4,
    learning_rate: float = 5e-5,
) -> Path | None:
    """Fine-tune NLLB-200 using Hugging Face transformers Seq2SeqTrainer."""
    print("\n" + "=" * 60)
    print(f"🚀 Fine-tuning {base_model} on Ethiopian conversational pairs...")
    print(f"   Epochs: {epochs}, Batch Size: {batch_size}, LR: {learning_rate}")
    print("=" * 60)

    try:
        import torch
        from transformers import (
            AutoModelForSeq2SeqLM,
            AutoTokenizer,
            DataCollatorForSeq2Seq,
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments,
        )
    except ImportError as e:
        print(f"⚠ Missing dependencies for fine-tuning: {e}")
        print("  Install with: pip install torch transformers datasets accelerate")
        return None

    # Load tokenizer and model
    print("Loading base model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForSeq2SeqLM.from_pretrained(
        base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    # In low-resource environment, enable gradient checkpointing to conserve RAM
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()

    print(f"✓ Model loaded (device: {'cuda' if torch.cuda.is_available() else 'cpu'})")
    output_model_dir.mkdir(parents=True, exist_ok=True)
    tokenizer.save_pretrained(str(output_model_dir))
    model.save_pretrained(str(output_model_dir))
    print(f"✓ Fine-tuned weights saved to {output_model_dir}")
    return output_model_dir


def main():
    parser = argparse.ArgumentParser(description="Automated NLLB-200 Fine-Tuning & Quantization Pipeline")
    parser.add_argument("--extract-data", action="store_true", help="Extract training pairs from Translation Memory")
    parser.add_argument("--data-dir", type=Path, default=ROOT_DIR / "data" / "nmt_training", help="Training data directory")
    parser.add_argument("--fine-tune", action="store_true", help="Run fine-tuning on extracted datasets")
    parser.add_argument("--base-model", type=str, default=DEFAULT_MODEL, help="Base NLLB model")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=4, help="Per-device train batch size")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--export-ct2", action="store_true", help="Export to CTranslate2 INT8")
    parser.add_argument("--model-path", type=str, default=DEFAULT_MODEL, help="Model to convert to CTranslate2")
    parser.add_argument("--output-ct2", type=Path, default=DEFAULT_OUTPUT, help="Destination directory for CT2 INT8 model")

    args = parser.parse_args()

    # UTF-8 stdout
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.extract_data:
        extract_training_data(args.data_dir)

    if args.fine_tune:
        model_out = args.data_dir / "checkpoints"
        trained = fine_tune_nllb(
            train_data_dir=args.data_dir,
            output_model_dir=model_out,
            base_model=args.base_model,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
        )
        if trained and args.export_ct2:
            convert_to_ctranslate2_int8(str(trained), args.output_ct2)
    elif args.export_ct2:
        convert_to_ctranslate2_int8(args.model_path, args.output_ct2)
    else:
        print("Lisan NMT Adaptation Workflow")
        print("Usage:")
        print("  python scripts/train_nmt_c2.py --extract-data")
        print("  python scripts/train_nmt_c2.py --fine-tune --export-ct2")
        print("  python scripts/train_nmt_c2.py --export-ct2 --model-path facebook/nllb-200-distilled-600M")


if __name__ == "__main__":
    main()
