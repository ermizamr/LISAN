"""
LISAN AI: Text-to-Speech (TTS) Verification & Benchmarking Suite.

Tests and benchmarks neural speech synthesis across all 5 supported languages:
- Amharic (አማርኛ) — facebook/mms-tts-amh
- Afaan Oromo — facebook/mms-tts-orm / facebook/mms-tts-gaz
- Tigrinya (ትግርኛ) — facebook/mms-tts-tir
- Somali (Soomaali) — facebook/mms-tts-som
- English — facebook/mms-tts-eng / piper-tts

Measures:
- Synthesis latency (seconds)
- Audio duration (seconds)
- Real-Time Factor (RTF = latency / duration, where RTF < 1.0 means faster than real-time)
- Output WAV file integrity

Usage:
    python scripts/benchmark_tts.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

OUTPUT_DIR = ROOT_DIR / "output_tts"

TEST_UTTERANCES = [
    {
        "lang": "amh",
        "lang_name": "Amharic",
        "text": "ሰላም ጤና ይስጥልኝ! በአቅራቢያው የሚገኘው ሆስፒታል የት ነው?",
        "model": "facebook/mms-tts-amh",
    },
    {
        "lang": "orm",
        "lang_name": "Afaan Oromo",
        "text": "Akkam jirtu! Hospitaalli naannoo kana jiru eessa jira?",
        "model": "facebook/mms-tts-orm",
    },
    {
        "lang": "tir",
        "lang_name": "Tigrinya",
        "text": "ሰላም ከመይ ኣለኹም! ኣብዚ ከባቢ ዝርከብ ሆስፒታል ኣበይ ኣሎ?",
        "model": "facebook/mms-tts-tir",
    },
    {
        "lang": "som",
        "lang_name": "Somali",
        "text": "Iska warran! Xaggee bay ku taallaa cisbitaalka kuugu dhow?",
        "model": "facebook/mms-tts-som",
    },
    {
        "lang": "eng",
        "lang_name": "English",
        "text": "Hello and welcome! Where is the nearest emergency hospital?",
        "model": "facebook/mms-tts-eng",
    },
]


def main():
    print("=" * 80)
    print("       LISAN AI — TEXT-TO-SPEECH (TTS) BENCHMARKING SUITE")
    print("=" * 80)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    from ai_pipeline.pipeline import MMSTTSEngine
    tts = MMSTTSEngine()
    tts.load(preload_langs=["amh", "orm", "tir", "som", "eng"])

    import soundfile as sf

    results = []
    print("\nSynthesizing speech across all 5 languages...")
    print("-" * 80)

    for item in TEST_UTTERANCES:
        lang = item["lang"]
        lang_name = item["lang_name"]
        text = item["text"]
        model = item["model"]

        out_file = OUTPUT_DIR / f"test_{lang}.wav"

        t0 = time.time()
        try:
            wav_bytes = tts.synthesize_wav(text, lang=lang)
            with open(out_file, "wb") as f:
                f.write(wav_bytes)
            latency = time.time() - t0

            # Inspect output audio file
            data, sr = sf.read(str(out_file))
            audio_duration = len(data) / sr
            rtf = latency / audio_duration if audio_duration > 0 else 0.0
            status = "✓ OK" if len(wav_bytes) > 1000 else "✗ EMPTY"
        except Exception as e:
            latency = time.time() - t0
            audio_duration = 0.0
            rtf = 0.0
            status = f"✗ ERROR: {e}"

        results.append({
            "lang": lang,
            "lang_name": lang_name,
            "text": text,
            "latency": latency,
            "duration": audio_duration,
            "rtf": rtf,
            "status": status,
            "file": str(out_file.relative_to(ROOT_DIR)),
        })

        print(f"[{lang.upper()}] {lang_name:<12} | Time: {latency:.2f}s | Audio: {audio_duration:.2f}s | RTF: {rtf:.2f}x | {status}")
        print(f"  • Text : '{text}'")
        print(f"  • File : {out_file.name} ({len(wav_bytes) if 'wav_bytes' in locals() else 0:,} bytes)\n")

    print("=" * 80)
    print("                        TTS SCORECARD")
    print("=" * 80)
    print(f"{'Language':<14} | {'Synthesis Time':<14} | {'Audio Duration':<14} | {'RTF (Latency/Dur)':<18} | {'Status'}")
    print("-" * 80)

    for r in results:
        rtf_str = f"{r['rtf']:.2f}x (Real-time)" if r['rtf'] < 1.0 else f"{r['rtf']:.2f}x"
        print(f"{r['lang_name']:<14} | {r['latency']:>11.2f}s   | {r['duration']:>11.2f}s   | {rtf_str:<18} | {r['status']}")

    print("-" * 80)
    print(f"✓ All generated audio samples saved in: {OUTPUT_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()
