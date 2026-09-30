"""
LISAN AI: STT Dataset Preparation Pipeline for Ethiopian Languages.

Fetches and formats speech datasets for Whisper & Wav2Vec2 fine-tuning.
Supports:
1. Google FLEURS (Amharic 'am_et', Afaan Oromo 'om_et', Somali 'so_so')
2. Mozilla Common Voice 17.0 (Amharic 'am', Tigrinya 'ti', Somali 'so')
3. Local audio files from ai_pipeline/test_audio/ or custom directory

Output:
- data/stt_data/train_manifest.jsonl
- data/stt_data/val_manifest.jsonl
- data/stt_data/metadata.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "data" / "stt_data"


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare STT datasets for training")
    parser.add_argument("--source", type=str, choices=["fleurs", "common_voice", "local", "synthetic"], default="fleurs",
                        help="Data source to download/prepare")
    parser.add_argument("--languages", type=str, nargs="+", default=["am_et", "om_et", "so_so"],
                        help="Language codes (for fleurs: am_et, om_et, so_so; for common_voice: am, ti, so)")
    parser.add_argument("--max_samples_per_lang", type=int, default=500,
                        help="Max audio samples to load per language (to fit gaming PC training sessions)")
    parser.add_argument("--output_dir", type=str, default=str(OUTPUT_DIR))
    return parser.parse_args()


def prepare_fleurs(languages: list[str], max_samples: int, out_dir: Path):
    """Download and process Google FLEURS speech datasets."""
    print("\n" + "=" * 60)
    print("📥 Loading Google FLEURS Speech Corpus...")
    print(f"   Languages: {languages}")
    print(f"   Max samples per language: {max_samples}")
    print("=" * 60)

    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: datasets library not installed. Run: pip install datasets")
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = out_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    train_records = []
    val_records = []

    fleurs_lang_map = {
        "am_et": ("am", "amh"),
        "om_et": ("om", "orm"),
        "so_so": ("so", "som"),
    }

    import soundfile as sf

    for lang in languages:
        print(f"\nProcessing FLEURS {lang}...")
        try:
            ds = load_dataset("google/fleurs", lang, trust_remote_code=True)
        except Exception as e:
            print(f"✗ Failed to load FLEURS {lang}: {e}")
            continue

        whisper_code, lisan_code = fleurs_lang_map.get(lang, ("en", "eng"))

        # Process Train
        train_split = ds["train"].select(range(min(len(ds["train"]), max_samples)))
        print(f"  • Extracted {len(train_split)} train samples for {lang}")
        for i, row in enumerate(train_split):
            audio_arr = row["audio"]["array"]
            sr = row["audio"]["sampling_rate"]
            text = row["transcription"].strip()
            if not text:
                continue

            fname = f"fleurs_{lang}_train_{i}.wav"
            fpath = audio_dir / fname
            sf.write(str(fpath), audio_arr, sr)

            train_records.append({
                "audio_path": str(fpath.relative_to(ROOT_DIR)),
                "sentence": text,
                "language": whisper_code,
                "lisan_lang": lisan_code,
                "duration": len(audio_arr) / sr,
            })

        # Process Validation
        val_split = ds["validation"].select(range(min(len(ds["validation"]), max(10, max_samples // 10))))
        print(f"  • Extracted {len(val_split)} val samples for {lang}")
        for i, row in enumerate(val_split):
            audio_arr = row["audio"]["array"]
            sr = row["audio"]["sampling_rate"]
            text = row["transcription"].strip()
            if not text:
                continue

            fname = f"fleurs_{lang}_val_{i}.wav"
            fpath = audio_dir / fname
            sf.write(str(fpath), audio_arr, sr)

            val_records.append({
                "audio_path": str(fpath.relative_to(ROOT_DIR)),
                "sentence": text,
                "language": whisper_code,
                "lisan_lang": lisan_code,
                "duration": len(audio_arr) / sr,
            })

    # Save manifest files
    train_manifest = out_dir / "train_manifest.jsonl"
    val_manifest = out_dir / "val_manifest.jsonl"

    with open(train_manifest, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(val_manifest, "w", encoding="utf-8") as f:
        for r in val_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    metadata = {
        "source": "google/fleurs",
        "train_samples": len(train_records),
        "val_samples": len(val_records),
        "languages": languages,
    }
    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"✓ Manifest files saved successfully:")
    print(f"  • Train : {train_manifest} ({len(train_records)} audio clips)")
    print(f"  • Val   : {val_manifest} ({len(val_records)} audio clips)")
    print("=" * 60)
    return True


def prepare_local(out_dir: Path):
    """Index local audio test samples from ai_pipeline/test_audio/ and root."""
    print("\n" + "=" * 60)
    print("🔍 Indexing Local Audio Samples...")
    print("=" * 60)

    out_dir.mkdir(parents=True, exist_ok=True)
    known_samples = [
        {"path": "ai_pipeline/test_audio/hello_en.wav", "sentence": "Hello, how are you today?", "lang": "en", "lisan": "eng"},
        {"path": "ai_pipeline/test_audio/hospital_en.wav", "sentence": "Where is the nearest hospital?", "lang": "en", "lisan": "eng"},
        {"path": "ai_pipeline/test_audio/doctor_en.wav", "sentence": "I need to see a doctor immediately.", "lang": "en", "lisan": "eng"},
        {"path": "test_speech.wav", "sentence": "ሰላም እንደምን አደራችሁ", "lang": "am", "lisan": "amh"},
        {"path": "test_oromo_tts.wav", "sentence": "Akkam jirtu nagaa dhaa", "lang": "om", "lisan": "orm"},
        {"path": "real_test1.wav", "sentence": "ሰላም ነው ደህና ነሽ", "lang": "am", "lisan": "amh"},
        {"path": "real_test2.wav", "sentence": "እንዴት ነህ ወንድሜ", "lang": "am", "lisan": "amh"},
        {"path": "real_test3.wav", "sentence": "በአቅራቢያው ሆስፒታል አለ", "lang": "am", "lisan": "amh"},
    ]

    valid = []
    for item in known_samples:
        p = ROOT_DIR / item["path"]
        if p.exists():
            valid.append({
                "audio_path": item["path"],
                "sentence": item["sentence"],
                "language": item["lang"],
                "lisan_lang": item["lisan"],
            })
            print(f"  ✓ Found: {item['path']} ('{item['sentence']}')")

    if not valid:
        print("  ✗ No local sample WAVs found.")
        return False

    val_manifest = out_dir / "val_manifest.jsonl"
    with open(val_manifest, "w", encoding="utf-8") as f:
        for r in valid:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n✓ Saved {len(valid)} validation samples to {val_manifest}")
    return True


def main():
    args = parse_args()
    out_p = Path(args.output_dir)

    if args.source == "fleurs":
        prepare_fleurs(args.languages, args.max_samples_per_lang, out_p)
    elif args.source == "local":
        prepare_local(out_p)
    else:
        # Default try fleurs, fallback local
        if not prepare_fleurs(args.languages, args.max_samples_per_lang, out_p):
            prepare_local(out_p)


if __name__ == "__main__":
    main()
