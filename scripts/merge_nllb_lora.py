"""
LISAN AI: Merge NLLB-200 LoRA Adapter into Standalone Checkpoint and CTranslate2 INT8.

Loads base NLLB model (facebook/nllb-200-distilled-600M) and applies the trained LoRA adapter
weights from models_optimized/nllb_lora_adapter, producing:
1. Standalone Hugging Face checkpoint at models_optimized/nllb_ethio_finetuned
2. Ultra-fast CTranslate2 INT8 model at models_optimized/nllb_ctranslate2_int8

Usage:
    python scripts/merge_nllb_lora.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent

# Neutralize torchao version conflict in Google Colab / cloud environments
try:
    import peft.import_utils
    orig_is_torchao = getattr(peft.import_utils, "is_torchao_available", None)
    def _safe_is_torchao():
        try:
            return orig_is_torchao() if orig_is_torchao else False
        except ImportError:
            return False
    peft.import_utils.is_torchao_available = _safe_is_torchao
except Exception:
    pass


def parse_args():
    parser = argparse.ArgumentParser(description="Merge NLLB LoRA adapter into standalone checkpoint and CTranslate2")
    parser.add_argument("--base_model", type=str, default="facebook/nllb-200-distilled-600M",
                        help="Base NLLB model ID")
    parser.add_argument("--adapter_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "nllb_lora_adapter"),
                        help="Directory containing trained LoRA adapter")
    parser.add_argument("--merged_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "nllb_ethio_finetuned"),
                        help="Directory to save standalone merged model")
    parser.add_argument("--export_c2_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "nllb_ctranslate2_int8"),
                        help="Directory to export CTranslate2 INT8 model")
    return parser.parse_args()


def convert_to_ctranslate2(model_dir: str, output_dir: str) -> bool:
    print("\n" + "=" * 60)
    print("⚡ Converting Merged NLLB to CTranslate2 INT8...")
    print(f"   Source : {model_dir}")
    print(f"   Target : {output_dir}")
    print("=" * 60)
    try:
        import ctranslate2
    except ImportError:
        print("WARNING: ctranslate2 not installed. Run: pip install ctranslate2")
        return False

    cmd = [
        sys.executable, "-m", "ctranslate2.converters.transformers",
        "--model", model_dir,
        "--output_dir", output_dir,
        "--quantization", "int8",
        "--force",
    ]

    try:
        res = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ CTranslate2 INT8 conversion complete!")
        print(f"✓ Optimized model ready at: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ CTranslate2 conversion failed: {e.stderr}")
        return False


def merge_nllb(base_model_name: str, adapter_dir: str, merged_dir: str, c2_dir: str):
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    from peft import PeftModel

    adapter_p = Path(adapter_dir)
    merged_p = Path(merged_dir)

    print("=" * 70)
    print("       LISAN AI: NLLB LORA WEIGHT MERGE & INT8 EXPORT")
    print("=" * 70)
    print(f"Base NLLB Model    : {base_model_name}")
    print(f"Adapter Directory  : {adapter_p}")
    print(f"Merged Output Dir  : {merged_p}")
    print(f"CTranslate2 Dir    : {c2_dir}")

    if not adapter_p.exists():
        print(f"ERROR: Adapter directory {adapter_p} does not exist!")
        sys.exit(1)

    cuda_avail = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
    print(f"Device             : {device_name}")
    print("=" * 70)

    print(f"\n1. Loading clean base NLLB model: {base_model_name}...")
    base_model = AutoModelForSeq2SeqLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16 if cuda_avail else torch.float32,
        device_map="auto" if cuda_avail else None,
        low_cpu_mem_usage=True,
    )

    print(f"2. Loading NLLB tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(str(adapter_p))
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(base_model_name)

    print(f"3. Applying LoRA adapter from {adapter_p}...")
    peft_model = PeftModel.from_pretrained(
        base_model,
        str(adapter_p),
        is_trainable=False,
    )

    print("4. Merging weights into base model (merge_and_unload)...")
    merged_model = peft_model.merge_and_unload()

    print(f"5. Saving standalone merged checkpoint to {merged_p}...")
    merged_p.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(str(merged_p))
    tokenizer.save_pretrained(str(merged_p))

    del base_model
    del peft_model
    del merged_model
    if cuda_avail:
        torch.cuda.empty_cache()

    print("\n6. Exporting to CTranslate2 INT8...")
    convert_to_ctranslate2(str(merged_p), c2_dir)

    print("\n" + "=" * 70)
    print("🎉 SUCCESS: Standalone NLLB Translation model is ready!")
    print(f"  HF Checkpoint  : {merged_p}")
    print(f"  CTranslate2 INT8: {c2_dir}")
    print("=" * 70)


def main():
    args = parse_args()
    merge_nllb(args.base_model, args.adapter_dir, args.merged_dir, args.export_c2_dir)


if __name__ == "__main__":
    main()
