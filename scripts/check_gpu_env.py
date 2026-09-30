"""
LISAN AI: GPU Hardware & Training Environment Diagnostics.

Run this script to verify GPU acceleration, CUDA drivers, PyTorch capability,
and get auto-tuned hyperparameter recommendations for fine-tuning.

Usage:
    python scripts/check_gpu_env.py
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def check_environment():
    print("=" * 70)
    print("       LISAN AI — GPU HARDWARE & TRAINING DIAGNOSTICS")
    print("=" * 70)

    # 1. System Info
    os_info = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"
    py_info = f"{platform.python_implementation()} {platform.python_version()}"
    print(f"OS Platform     : {os_info}")
    print(f"Python Version  : {py_info}")
    print(f"Working Dir     : {Path.cwd()}")

    # 2. PyTorch & CUDA Check
    print("-" * 70)
    try:
        import torch
        torch_ver = torch.__version__
        cuda_avail = torch.cuda.is_available()
        print(f"PyTorch Version : {torch_ver}")
        print(f"CUDA Available  : {'✓ YES' if cuda_avail else '✗ NO (Running on CPU)'}")

        if cuda_avail:
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            gpu_props = torch.cuda.get_device_properties(0)
            vram_gb = gpu_props.total_memory / (1024 ** 3)
            compute_cap = f"{gpu_props.major}.{gpu_props.minor}"
            cuda_ver = torch.version.cuda
            bf16_supported = torch.cuda.is_bf16_supported()

            print(f"GPU Model       : {gpu_name} ({gpu_count} device detected)")
            print(f"VRAM Available  : {vram_gb:.2f} GB")
            print(f"Compute Cap     : SM {compute_cap}")
            print(f"PyTorch CUDA    : {cuda_ver}")
            print(f"bfloat16 Support: {'✓ Supported' if bf16_supported else '✗ Not supported (use float16)'}")

            # Test Memory Allocation
            try:
                x = torch.zeros((1000, 1000), device="cuda", dtype=torch.float16)
                torch.cuda.synchronize()
                print("CUDA Alloc Test : ✓ Passed (Tensor created on CUDA device)")
                del x
                torch.cuda.empty_cache()
            except Exception as e:
                print(f"CUDA Alloc Test : ✗ FAILED: {e}")
        else:
            print("\n[!] WARNING: PyTorch was installed without CUDA support!")
            print("    To enable GPU training on an NVIDIA card, run:")
            print("    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
            vram_gb = 0.0
            bf16_supported = False
    except ImportError:
        print("PyTorch Version : ✗ NOT INSTALLED")
        vram_gb = 0.0
        bf16_supported = False

    # 3. BitsAndBytes (4-bit QLoRA) Check
    print("-" * 70)
    try:
        import bitsandbytes as bnb
        bnb_ver = getattr(bnb, "__version__", "unknown")
        print(f"BitsAndBytes    : ✓ Installed (v{bnb_ver})")
    except Exception as e:
        print(f"BitsAndBytes    : ✗ Not working ({e})")
        print("    Run: pip install bitsandbytes>=0.43.0")

    # 4. CTranslate2 Check
    try:
        import ctranslate2
        ct2_ver = ctranslate2.__version__
        cuda_count = ctranslate2.get_cuda_device_count() if hasattr(ctranslate2, "get_cuda_device_count") else 0
        print(f"CTranslate2     : ✓ Installed (v{ct2_ver}) — CUDA devices: {cuda_count}")
    except Exception as e:
        print(f"CTranslate2     : ✗ Not installed ({e})")

    # 5. Audio & STT / TTS Libraries Check
    print("-" * 70)
    pkgs = {
        "transformers": "Transformers",
        "peft": "PEFT (LoRA)",
        "datasets": "HuggingFace Datasets",
        "accelerate": "Accelerate",
        "soundfile": "SoundFile",
        "pyctcdecode": "PyCTCDecode (CTC Beam Search)",
        "jiwer": "JiWER (STT WER Metrics)",
        "sacrebleu": "SacreBLEU (NMT BLEU Metrics)",
    }
    for mod, name in pkgs.items():
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "installed")
            print(f"{name:<20}: ✓ v{ver}")
        except ImportError:
            print(f"{name:<20}: ✗ Missing (pip install {mod})")

    # 6. Auto-Tuned Recommendations
    print("=" * 70)
    print("       OPTIMAL TRAINING HYPERPARAMETERS FOR THIS HARDWARE")
    print("=" * 70)
    if vram_gb >= 18:
        tier = "HIGH TIER (RTX 3090, 4090, A10G, 24GB VRAM)"
        nmt_batch = 32
        nmt_accum = 1
        nmt_quant = "4bit or fp16/bf16"
        stt_batch = 16
        stt_accum = 2
        stt_model = "openai/whisper-small or whisper-medium"
    elif vram_gb >= 11:
        tier = "MID TIER (RTX 3060 12GB, RTX 3080 12GB, RTX 4070 12GB)"
        nmt_batch = 16
        nmt_accum = 2
        nmt_quant = "4bit (QLoRA)"
        stt_batch = 8
        stt_accum = 4
        stt_model = "openai/whisper-small"
    elif vram_gb >= 7:
        tier = "STANDARD TIER (RTX 3060/3070 8GB, RTX 4060 8GB)"
        nmt_batch = 8
        nmt_accum = 4
        nmt_quant = "4bit (QLoRA)"
        stt_batch = 4
        stt_accum = 8
        stt_model = "openai/whisper-base or whisper-small"
    else:
        tier = "CPU / ENTRY TIER (<6GB VRAM)"
        nmt_batch = 4
        nmt_accum = 8
        nmt_quant = "4bit or CPU fallback"
        stt_batch = 2
        stt_accum = 16
        stt_model = "openai/whisper-tiny"

    print(f"Hardware Class  : {tier}")
    print("\n[Machine Translation — NLLB-200 Fine-Tuning]:")
    print(f"  • Recommended Quantization : {nmt_quant}")
    print(f"  • Batch Size Per Device    : {nmt_batch}")
    print(f"  • Gradient Accumulation    : {nmt_accum}")
    print(f"  • Effective Batch Size     : {nmt_batch * nmt_accum}")
    print(f"  • Command to Run           : python scripts/train_nllb_lora.py --batch_size {nmt_batch} --grad_accum {nmt_accum} --merge_and_export")

    print("\n[Speech-to-Text — Whisper Fine-Tuning]:")
    print(f"  • Recommended Base Model   : {stt_model}")
    print(f"  • Batch Size               : {stt_batch}")
    print(f"  • Gradient Accumulation    : {stt_accum}")
    print(f"  • Command to Run           : python scripts/train_whisper_lora.py --base_model {stt_model} --batch_size {stt_batch} --grad_accum {stt_accum}")

    print("=" * 70)


if __name__ == "__main__":
    check_environment()
