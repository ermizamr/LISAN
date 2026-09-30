"""
LISAN AI: Merge Whisper LoRA Adapter into Standalone Checkpoint.

Loads base Whisper model (openai/whisper-small) and applies the trained LoRA adapter
weights from models_optimized/whisper_lora_adapter, producing a standalone Hugging Face
model at models_optimized/whisper_ethio_finetuned that requires no PEFT dependencies at inference time.

Usage:
    python scripts/merge_whisper_lora.py
"""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description="Merge Whisper LoRA adapter into standalone checkpoint")
    parser.add_argument("--base_model", type=str, default="openai/whisper-small",
                        help="Base Whisper model ID")
    parser.add_argument("--adapter_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "whisper_lora_adapter"),
                        help="Directory containing trained LoRA adapter")
    parser.add_argument("--merged_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "whisper_ethio_finetuned"),
                        help="Directory to save standalone merged model")
    return parser.parse_args()


def merge_whisper(base_model_name: str, adapter_dir: str, merged_dir: str):
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from peft import PeftModel

    adapter_p = Path(adapter_dir)
    merged_p = Path(merged_dir)

    print("=" * 70)
    print("       LISAN AI: WHISPER LORA WEIGHT MERGE")
    print("=" * 70)
    print(f"Base Whisper Model : {base_model_name}")
    print(f"Adapter Directory  : {adapter_p}")
    print(f"Merged Output Dir  : {merged_p}")

    if not adapter_p.exists():
        print(f"ERROR: Adapter directory {adapter_p} does not exist!")
        sys.exit(1)

    cuda_avail = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
    print(f"Device             : {device_name}")
    print("=" * 70)

    print(f"\n1. Loading clean base Whisper model: {base_model_name}...")
    base_model = WhisperForConditionalGeneration.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16 if cuda_avail else torch.float32,
        device_map="auto" if cuda_avail else None,
        low_cpu_mem_usage=True,
    )

    print(f"2. Loading Whisper processor...")
    try:
        processor = WhisperProcessor.from_pretrained(str(adapter_p))
    except Exception:
        processor = WhisperProcessor.from_pretrained(base_model_name, language="amharic", task="transcribe")

    print(f"3. Applying LoRA adapter from {adapter_p}...")
    try:
        import peft.import_utils
        peft.import_utils.is_torchao_available = lambda: False
    except Exception:
        pass
    try:
        import peft.tuners.lora.torchao as tao
        tao.dispatch_torchao = lambda *args, **kwargs: None
        tao.is_torchao_available = lambda: False
    except Exception:
        pass

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
    processor.save_pretrained(str(merged_p))

    print("\n" + "=" * 70)
    print("✓ SUCCESS: Standalone Whisper Ethiopian STT model is ready!")
    print(f"  Location: {merged_p}")
    print("=" * 70)


def main():
    args = parse_args()
    merge_whisper(args.base_model, args.adapter_dir, args.merged_dir)


if __name__ == "__main__":
    main()
