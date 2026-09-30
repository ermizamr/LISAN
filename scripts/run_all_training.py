"""
LISAN AI: Master Training, Fine-Tuning & Model Optimization Orchestrator.

One-stop command-line interface to train, merge, quantize, and verify all
three AI pillars on a GPU-enabled machine:
1. NMT Translation (NLLB-200 QLoRA -> Merged Model -> CTranslate2 INT8)
2. STT Speech Recognition (Data Prep -> Whisper LoRA -> Checkpoint Export -> WER Eval)
3. TTS Speech Synthesis (Neural Voice Verification -> RTF Benchmarking)

Usage:
    # Run everything end-to-end:
    python scripts/run_all_training.py --all

    # Or run step-by-step:
    python scripts/run_all_training.py --check-gpu
    python scripts/run_all_training.py --nmt
    python scripts/run_all_training.py --stt-prep
    python scripts/run_all_training.py --stt-train
    python scripts/run_all_training.py --stt-eval
    python scripts/run_all_training.py --tts-eval
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="LISAN AI: Master GPU Training Orchestrator")
    parser.add_argument("--all", action="store_true", help="Execute complete pipeline (GPU check -> NMT -> STT -> TTS -> Eval)")
    parser.add_argument("--check-gpu", action="store_true", help="Run GPU environment diagnostics")
    parser.add_argument("--nmt", action="store_true", help="Run NLLB-200 LoRA training, merge, and CTranslate2 export")
    parser.add_argument("--stt-prep", action="store_true", help="Download and prepare STT audio dataset")
    parser.add_argument("--stt-train", action="store_true", help="Run Whisper LoRA fine-tuning")
    parser.add_argument("--stt-eval", action="store_true", help="Evaluate STT latency and WER")
    parser.add_argument("--tts-eval", action="store_true", help="Verify and benchmark TTS synthesis across 5 languages")
    parser.add_argument("--eval-benchmarks", action="store_true", help="Run HornMT translation benchmarks")
    parser.add_argument("--epochs", type=int, default=3, help="Training epochs for NMT and STT")
    parser.add_argument("--batch_size", type=int, default=None, help="Batch size (default: auto-detected from VRAM)")
    parser.add_argument("--skip_stt_train", action="store_true", help="Skip STT training if prioritizing NMT")
    return parser.parse_args()


def run_cmd(cmd: list[str], desc: str) -> bool:
    print("\n" + "=" * 75)
    print(f"▶ STEP: {desc}")
    print(f"  Command: {' '.join(cmd)}")
    print("=" * 75)
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, check=True)
        dur = time.time() - t0
        print(f"✓ COMPLETED in {dur:.1f}s: {desc}")
        return True
    except subprocess.CalledProcessError as e:
        dur = time.time() - t0
        print(f"✗ FAILED in {dur:.1f}s with exit code {e.returncode}: {desc}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False


def main():
    args = parse_args()
    py = sys.executable

    # If no flags are passed, print help and run gpu check
    if not any([args.all, args.check_gpu, args.nmt, args.stt_prep, args.stt_train, args.stt_eval, args.tts_eval, args.eval_benchmarks]):
        print("LISAN AI Training Orchestrator — No step specified. Running GPU check...")
        args.check_gpu = True

    print("=" * 75)
    print("       LISAN AI — MASTER TRAINING & OPTIMIZATION PIPELINE")
    print("=" * 75)
    print(f"Python Executable : {py}")
    print(f"Project Root      : {ROOT_DIR}")
    print("=" * 75)

    # 1. GPU Check
    if args.all or args.check_gpu:
        run_cmd([py, str(ROOT_DIR / "scripts" / "check_gpu_env.py")], "GPU Hardware & Training Diagnostics")

    # 2. NMT Translation Training
    if args.all or args.nmt:
        nmt_cmd = [
            py,
            str(ROOT_DIR / "scripts" / "train_nllb_lora.py"),
            "--num_epochs", str(args.epochs),
            "--merge_and_export",
        ]
        if args.batch_size:
            nmt_cmd.extend(["--batch_size", str(args.batch_size)])
        run_cmd(nmt_cmd, "NLLB-200 Multilingual LoRA Training & CTranslate2 INT8 Export")

    # 3. STT Data Prep
    if args.all or args.stt_prep:
        run_cmd([py, str(ROOT_DIR / "scripts" / "prepare_stt_data.py"), "--source", "local"],
                "STT Dataset Preparation (Local Audio Test Manifest)")

    # 4. STT Whisper LoRA Training
    if (args.all and not args.skip_stt_train) or args.stt_train:
        stt_cmd = [
            py,
            str(ROOT_DIR / "scripts" / "train_whisper_lora.py"),
            "--num_epochs", str(args.epochs),
            "--merge_and_save",
        ]
        if args.batch_size:
            stt_cmd.extend(["--batch_size", str(args.batch_size)])
        run_cmd(stt_cmd, "Whisper STT LoRA Fine-Tuning & Weight Merging")

    # 5. STT Evaluation
    if args.all or args.stt_eval:
        run_cmd([py, str(ROOT_DIR / "scripts" / "evaluate_stt.py")], "STT Accuracy & Latency Evaluation")

    # 6. TTS Benchmarking
    if args.all or args.tts_eval:
        run_cmd([py, str(ROOT_DIR / "scripts" / "benchmark_tts.py")], "Text-to-Speech (TTS) Verification & RTF Benchmarking")

    # 7. Translation Benchmark Evaluation
    if args.all or args.eval_benchmarks:
        bench_script = ROOT_DIR / "scripts" / "evaluate_benchmarks.py"
        if bench_script.exists():
            run_cmd([py, str(bench_script), "--limit", "100"], "HornMT Translation Benchmark Evaluation")

    print("\n" + "=" * 75)
    print("🎉 ALL REQUESTED TRAINING & EVALUATION TASKS COMPLETED!")
    print("=" * 75)


if __name__ == "__main__":
    main()
