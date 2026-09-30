"""
LISAN AI: Comprehensive Speech-to-Text (STT) Evaluation Harness.

Benchmarks STT latency, transcription accuracy, Word Error Rate (WER),
and Character Error Rate (CER) across Ethiopian audio recordings.

Engines Tested:
1. DatasetEtHoheSTT (snapwre/hohe-asr-amharic) — Amharic native ASR
2. EthioMultilingualSTT (badrex/Ethio-ASR-multilingual-600M) — Amharic, Oromo, Tigrinya
3. WhisperSTT (OpenAI Whisper tiny/base/small/finetuned) — Multilingual STT

Usage:
    python scripts/evaluate_stt.py
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Known reference ground-truth audio test cases
TEST_CASES = [
    {
        "file": "ai_pipeline/test_audio/hello_en.wav",
        "reference": "hello how are you today",
        "lang": "eng",
        "description": "English Greeting",
    },
    {
        "file": "ai_pipeline/test_audio/hospital_en.wav",
        "reference": "where is the nearest hospital",
        "lang": "eng",
        "description": "English Medical Query",
    },
    {
        "file": "ai_pipeline/test_audio/doctor_en.wav",
        "reference": "i need to see a doctor immediately",
        "lang": "eng",
        "description": "English Emergency",
    },
    {
        "file": "test_speech.wav",
        "reference": "ሰላም እንደምን አደራችሁ",
        "lang": "amh",
        "description": "Amharic Morning Greeting",
    },
    {
        "file": "test_oromo_tts.wav",
        "reference": "akkam jirtu nagaa dhaa",
        "lang": "orm",
        "description": "Afaan Oromo Greeting",
    },
    {
        "file": "real_test1.wav",
        "reference": "ሰላም ነው ደህና ነሽ",
        "lang": "amh",
        "description": "Amharic Real Mic 1",
    },
    {
        "file": "real_test2.wav",
        "reference": "እንዴት ነህ ወንድሜ",
        "lang": "amh",
        "description": "Amharic Real Mic 2",
    },
]


def calculate_wer_cer(reference: str, hypothesis: str):
    """Compute Character Error Rate (CER) and Word Error Rate (WER)."""
    try:
        import jiwer
        wer = jiwer.wer(reference, hypothesis)
        cer = jiwer.cer(reference, hypothesis)
        return round(wer * 100, 1), round(cer * 100, 1)
    except Exception:
        # Fallback simple word overlap
        ref_words = set(reference.lower().split())
        hyp_words = set(hypothesis.lower().split())
        if not ref_words:
            return 0.0, 0.0
        overlap = len(ref_words.intersection(hyp_words))
        wer_est = max(0.0, (len(ref_words) - overlap) / len(ref_words) * 100)
        return round(wer_est, 1), round(wer_est, 1)


def main():
    print("=" * 80)
    print("       LISAN AI — SPEECH-TO-TEXT (STT) EVALUATION HARNESS")
    print("=" * 80)

    from ai_pipeline.pipeline import TranslatorPipeline
    pipeline = TranslatorPipeline(whisper_size="tiny")
    print("Loading STT models into memory...")
    pipeline.load_all()

    results = []
    print("\nRunning STT inference on test recordings...")
    print("-" * 80)

    for case in TEST_CASES:
        fpath = ROOT_DIR / case["file"]
        if not fpath.exists():
            continue

        lang = case["lang"]
        ref = case["reference"]
        desc = case["description"]

        t0 = time.time()
        try:
            hyp = pipeline.transcribe_audio(str(fpath), src_lang=lang)
        except Exception as e:
            hyp = f"ERROR: {e}"
        latency = time.time() - t0

        wer, cer = calculate_wer_cer(ref, hyp)

        results.append({
            "desc": desc,
            "lang": lang,
            "reference": ref,
            "hypothesis": hyp,
            "latency": latency,
            "wer": wer,
            "cer": cer,
        })

        print(f"[{lang.upper()}] {desc:<26} | Time: {latency:.2f}s | WER: {wer}%")
        print(f"  • Ref: {ref}")
        print(f"  • Hyp: {hyp}\n")

    print("=" * 80)
    print("                        SUMMARY SCORECARD")
    print("=" * 80)
    print(f"{'Test Case':<26} | {'Lang':<4} | {'Latency':<8} | {'WER':<7} | {'Status'}")
    print("-" * 80)

    avg_lat = sum(r["latency"] for r in results) / max(1, len(results))
    avg_wer = sum(r["wer"] for r in results) / max(1, len(results))

    for r in results:
        status = "✓ PASS" if r["wer"] <= 35.0 else ("⚠️ ACCEPTABLE" if r["wer"] <= 60.0 else "✗ HIGH WER")
        print(f"{r['desc']:<26} | {r['lang']:<4} | {r['latency']:>6.2f}s | {r['wer']:>5.1f}% | {status}")

    print("-" * 80)
    print(f"Average Latency : {avg_lat:.2f}s")
    print(f"Average WER     : {avg_wer:.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    main()
