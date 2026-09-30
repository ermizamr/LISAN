"""
Export SQLite Translation Memory to HuggingFace JSONL format for NLLB-200 LoRA Fine-Tuning.

Produces:
- data/training_data/train.jsonl (95%)
- data/training_data/val.jsonl (5%)
- data/training_data/metadata.json (statistics & language pair breakdown)

Maps local language codes to NLLB-200 FLORES codes:
- orm -> gaz_Latn (West Central Oromo)
- amh -> amh_Ethi (Amharic)
- tir -> tir_Ethi (Tigrinya)
- som -> som_Latn (Somali)
- eng -> eng_Latn (English)
"""

import json
import random
import sqlite3
import sys
from pathlib import Path

# Force UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "translation_memory.db"
OUTPUT_DIR = ROOT_DIR / "data" / "training_data"

NLLB_LANG_MAP = {
    "orm": "gaz_Latn",
    "amh": "amh_Ethi",
    "tir": "tir_Ethi",
    "som": "som_Latn",
    "eng": "eng_Latn",
}


def export_dataset(val_ratio: float = 0.05, seed: int = 42):
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train_path = OUTPUT_DIR / "train.jsonl"
    val_path = OUTPUT_DIR / "val.jsonl"
    meta_path = OUTPUT_DIR / "metadata.json"

    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT src_lang, tgt_lang, source_text, target_text, domain, confidence
        FROM translation_memory
        WHERE source_text IS NOT NULL AND target_text IS NOT NULL
    """)
    rows = cursor.fetchall()
    conn.close()

    print(f"Loaded {len(rows)} raw rows from database.")

    valid_samples = []
    pair_counts = {}

    for src_l, tgt_l, src_t, tgt_t, domain, conf in rows:
        src_l = src_l.strip().lower()
        tgt_l = tgt_l.strip().lower()
        src_t = src_t.strip()
        tgt_t = tgt_t.strip()

        if not src_t or not tgt_t:
            continue
        if src_l not in NLLB_LANG_MAP or tgt_l not in NLLB_LANG_MAP:
            continue
        if src_t == tgt_t:
            continue

        pair_key = f"{src_l}->{tgt_l}"
        pair_counts[pair_key] = pair_counts.get(pair_key, 0) + 1

        sample = {
            "source": src_t,
            "target": tgt_t,
            "src_lang": src_l,
            "tgt_lang": tgt_l,
            "src_nllb": NLLB_LANG_MAP[src_l],
            "tgt_nllb": NLLB_LANG_MAP[tgt_l],
            "domain": domain,
            "confidence": float(conf) if conf is not None else 1.0,
        }
        valid_samples.append(sample)

    print(f"Validated {len(valid_samples)} clean bilingual pairs across {len(pair_counts)} language directions.")

    # Shuffle with reproducible seed
    random.seed(seed)
    random.shuffle(valid_samples)

    val_size = int(len(valid_samples) * val_ratio)
    val_samples = valid_samples[:val_size]
    train_samples = valid_samples[val_size:]

    print(f"Splitting into {len(train_samples)} Train samples ({(1-val_ratio)*100:.0f}%) and {len(val_samples)} Val samples ({val_ratio*100:.0f}%)...")

    # Write train.jsonl
    with open(train_path, "w", encoding="utf-8") as f:
        for s in train_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Write val.jsonl
    with open(val_path, "w", encoding="utf-8") as f:
        for s in val_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    # Write metadata.json
    metadata = {
        "total_samples": len(valid_samples),
        "train_samples": len(train_samples),
        "val_samples": len(val_samples),
        "language_pairs": pair_counts,
        "nllb_lang_mapping": NLLB_LANG_MAP,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n=== Export Summary ===")
    print(f"Train File : {train_path} ({train_path.stat().st_size / (1024*1024):.2f} MB)")
    print(f"Val File   : {val_path} ({val_path.stat().st_size / (1024*1024):.2f} MB)")
    print(f"Metadata   : {meta_path}")
    print("Export complete successfully!")


if __name__ == "__main__":
    export_dataset()
