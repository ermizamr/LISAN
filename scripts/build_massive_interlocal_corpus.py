"""
LISAN AI: Massive Inter-Local Ethiopian Multilingual Corpus Builder.

Combines ALL available data resources:
1. data/raw_bitext/ (Over 1.24 Million parallel sentences):
   - Amharic <-> Afaan Oromo (109k)
   - Amharic <-> Somali (516k)
   - Amharic <-> Tigrinya (300k)
   - Afaan Oromo <-> Somali (88k)
   - Afaan Oromo <-> Tigrinya (58k)
   - Somali <-> Tigrinya (169k)
2. data/translation_memory.db (Conversational, kebele, market, clinic, police phrases)
3. Conversational Seeds & Idioms across all language directions

Filters by semantic similarity score (>= 1.05), deduplicates, balances,
and exports high-quality train.jsonl and val.jsonl.
"""

from __future__ import annotations

import csv
import json
import random
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT_DIR / "data" / "raw_bitext"
DB_PATH = ROOT_DIR / "data" / "translation_memory.db"
HORNMT_DIR = ROOT_DIR / "data" / "hornmt"
OUTPUT_DIR = ROOT_DIR / "data" / "training_data"

NLLB_MAP = {
    "orm": "gaz_Latn",
    "amh": "amh_Ethi",
    "tir": "tir_Ethi",
    "som": "som_Latn",
    "eng": "eng_Latn",
}

RAW_FILES = [
    {"file": "amharic-oromo.csv", "src": "amh", "tgt": "orm", "src_col": "Amharic", "tgt_col": "Oromo"},
    {"file": "amharic-somali.csv", "src": "amh", "tgt": "som", "src_col": "Amharic", "tgt_col": "Somali"},
    {"file": "amharic-tigrinya.csv", "src": "amh", "tgt": "tir", "src_col": "Amharic", "tgt_col": "Tigrinya"},
    {"file": "oromo-somali.csv", "src": "orm", "tgt": "som", "src_col": "Oromo", "tgt_col": "Somali"},
    {"file": "oromo-tigrinya.csv", "src": "orm", "tgt": "tir", "src_col": "Oromo", "tgt_col": "Tigrinya"},
    {"file": "somali-tigrinya.csv", "src": "som", "tgt": "tir", "src_col": "Somali", "tgt_col": "Tigrinya"},
]

ETHIOPIC_REGEX = re.compile(r"[\u1200-\u137F]")
LATIN_REGEX = re.compile(r"[a-zA-Z]")


def is_valid_script(text: str, lang: str) -> bool:
    """Verify text matches the expected writing script of the language."""
    if lang in ("amh", "tir"):
        return bool(ETHIOPIC_REGEX.search(text))
    elif lang in ("orm", "som", "eng"):
        return bool(LATIN_REGEX.search(text))
    return True


def clean_text(text: str) -> str:
    """Clean whitespace, quotes, and normalize Unicode."""
    text = text.strip().strip('"').strip("'").strip()
    text = re.sub(r"\s+", " ", text)
    # Normalize Oromo hudhaa quotes
    text = re.sub(r"[’‘`´ʻʼ]", "'", text)
    return text


def build_massive_corpus(target_per_direction: int = 8000, min_score: float = 1.05, val_ratio: float = 0.05):
    print("=" * 75)
    print("       LISAN AI — MASSIVE MULTILINGUAL CORPUS BUILDER (EXPANDED)")
    print("=" * 75)

    pairs_pool = defaultdict(list)
    seen_hashes = set()

    # 1. Ingest Gold Standard HornMT Corpus (first 1,500 lines for training, reserve rest)
    if HORNMT_DIR.exists():
        print(f"Ingesting 5-Way HornMT Gold Parallel Corpus from {HORNMT_DIR}...")
        horn_langs = ["amh", "eng", "orm", "som", "tir"]
        horn_texts = {}
        for l in horn_langs:
            txt_file = HORNMT_DIR / f"{l}.txt"
            if txt_file.exists():
                horn_texts[l] = [line.strip() for line in txt_file.read_text(encoding="utf-8").splitlines()]

        # Use first 1500 parallel lines for training
        num_horn_lines = min(len(horn_texts[l]) for l in horn_langs) if len(horn_texts) == 5 else 0
        train_horn_limit = min(num_horn_lines, 1500)
        horn_added = 0

        for idx in range(train_horn_limit):
            for s_l in horn_langs:
                for t_l in horn_langs:
                    if s_l == t_l:
                        continue
                    s_t = clean_text(horn_texts[s_l][idx])
                    t_t = clean_text(horn_texts[t_l][idx])
                    if not s_t or not t_t or s_t == t_t:
                        continue
                    if not is_valid_script(s_t, s_l) or not is_valid_script(t_t, t_l):
                        continue
                    h_key = f"{s_l}:{s_t}:{t_l}:{t_t}"
                    if h_key not in seen_hashes:
                        seen_hashes.add(h_key)
                        p_key = f"{s_l}->{t_l}"
                        pairs_pool[p_key].append({
                            "source": s_t,
                            "target": t_t,
                            "src_lang": s_l,
                            "tgt_lang": t_l,
                            "src_nllb": NLLB_MAP[s_l],
                            "tgt_nllb": NLLB_MAP[t_l],
                            "domain": "hornmt_gold",
                            "confidence": 1.0,
                        })
                        horn_added += 1
        print(f"  • Ingested {horn_added:,} HornMT gold sentence pairs across all 20 directions.")

    # 2. Ingest Translation Memory DB (High confidence, conversational focus)
    if DB_PATH.exists():
        print(f"\nConnecting to Translation Memory DB ({DB_PATH.name})...")
        conn = sqlite3.connect(str(DB_PATH))
        cur = conn.cursor()
        cur.execute("""
            SELECT src_lang, tgt_lang, source_text, target_text, domain, confidence
            FROM translation_memory
            WHERE source_text IS NOT NULL AND target_text IS NOT NULL
        """)
        tm_rows = cur.fetchall()
        conn.close()
        print(f"  • Found {len(tm_rows):,} TM entries.")

        for src_l, tgt_l, s_t, t_t, domain, conf in tm_rows:
            src_l = src_l.strip().lower()
            tgt_l = tgt_l.strip().lower()
            s_t = clean_text(s_t)
            t_t = clean_text(t_t)

            if not s_t or not t_t or s_t == t_t:
                continue
            if src_l not in NLLB_MAP or tgt_l not in NLLB_MAP:
                continue
            if not is_valid_script(s_t, src_l) or not is_valid_script(t_t, tgt_l):
                continue

            pair_key = f"{src_l}->{tgt_l}"
            hash_key = f"{src_l}:{s_t}:{tgt_l}:{t_t}"
            if hash_key in seen_hashes:
                continue
            seen_hashes.add(hash_key)

            pairs_pool[pair_key].append({
                "source": s_t,
                "target": t_t,
                "src_lang": src_l,
                "tgt_lang": tgt_l,
                "src_nllb": NLLB_MAP[src_l],
                "tgt_nllb": NLLB_MAP[tgt_l],
                "domain": domain or "conversational_tm",
                "confidence": float(conf) if conf else 1.0,
            })

    # 3. Ingest raw bitext CSVs (Amharic, Oromo, Tigrinya, Somali pairs)
    if RAW_DIR.exists():
        print(f"\nProcessing raw parallel bitext from {RAW_DIR}...")
        for meta in RAW_FILES:
            csv_path = RAW_DIR / meta["file"]
            if not csv_path.exists():
                continue

            src_code = meta["src"]
            tgt_code = meta["tgt"]
            src_col = meta["src_col"]
            tgt_col = meta["tgt_col"]

            print(f"  • Reading {meta['file']} ({src_code} <-> {tgt_code})...", end="", flush=True)
            added_count = 0

            with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        score = float(row.get("score", 1.1))
                    except ValueError:
                        score = 1.1

                    if score < min_score:
                        continue

                    s_t = clean_text(row.get(src_col, ""))
                    t_t = clean_text(row.get(tgt_col, ""))

                    if not s_t or not t_t or s_t == t_t:
                        continue
                    # Word length sanity (skip extreme anomalies)
                    s_words = len(s_t.split())
                    t_words = len(t_t.split())
                    if s_words < 2 or t_words < 2 or s_words > 60 or t_words > 60:
                        continue
                    # Script validity check
                    if not is_valid_script(s_t, src_code) or not is_valid_script(t_t, tgt_code):
                        continue
                    # Length ratio filter (filter misaligned bitext)
                    if max(s_words / t_words, t_words / s_words) > 2.5:
                        continue

                    # Forward: src -> tgt
                    k_fwd = f"{src_code}->{tgt_code}"
                    h_fwd = f"{src_code}:{s_t}:{tgt_code}:{t_t}"
                    if h_fwd not in seen_hashes and len(pairs_pool[k_fwd]) < target_per_direction:
                        seen_hashes.add(h_fwd)
                        pairs_pool[k_fwd].append({
                            "source": s_t,
                            "target": t_t,
                            "src_lang": src_code,
                            "tgt_lang": tgt_code,
                            "src_nllb": NLLB_MAP[src_code],
                            "tgt_nllb": NLLB_MAP[tgt_code],
                            "domain": "interlocal_bitext",
                            "confidence": min(1.0, round(score / 1.25, 2)),
                        })
                        added_count += 1

                    # Backward: tgt -> src
                    k_rev = f"{tgt_code}->{src_code}"
                    h_rev = f"{tgt_code}:{t_t}:{src_code}:{s_t}"
                    if h_rev not in seen_hashes and len(pairs_pool[k_rev]) < target_per_direction:
                        seen_hashes.add(h_rev)
                        pairs_pool[k_rev].append({
                            "source": t_t,
                            "target": s_t,
                            "src_lang": tgt_code,
                            "tgt_lang": src_code,
                            "src_nllb": NLLB_MAP[tgt_code],
                            "tgt_nllb": NLLB_MAP[src_code],
                            "domain": "interlocal_bitext",
                            "confidence": min(1.0, round(score / 1.25, 2)),
                        })
                        added_count += 1

            print(f" added {added_count:,} pairs.")

    # 3. Balance and Combine
    print("\n" + "=" * 75)
    print("                     DATASET COMPOSITION SCORECARD")
    print("=" * 75)

    all_samples = []
    final_pair_counts = {}

    for pair_key, samples in sorted(pairs_pool.items()):
        random.seed(42)
        random.shuffle(samples)
        selected = samples[:target_per_direction]
        final_pair_counts[pair_key] = len(selected)
        all_samples.extend(selected)
        print(f"  • {pair_key:10}: {len(selected):>6,} sentences")

    random.seed(42)
    random.shuffle(all_samples)

    val_count = int(len(all_samples) * val_ratio)
    val_set = all_samples[:val_count]
    train_set = all_samples[val_count:]

    print("-" * 75)
    print(f"Total Clean Parallel Samples : {len(all_samples):,}")
    print(f"Training Samples (95%)       : {len(train_set):,}")
    print(f"Validation Samples (5%)      : {len(val_set):,}")
    print("=" * 75)

    # 4. Save to files
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train_file = OUTPUT_DIR / "train.jsonl"
    val_file = OUTPUT_DIR / "val.jsonl"
    meta_file = OUTPUT_DIR / "metadata.json"

    print("Writing files...")
    with open(train_file, "w", encoding="utf-8") as f:
        for s in train_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    with open(val_file, "w", encoding="utf-8") as f:
        for s in val_set:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    metadata = {
        "total_samples": len(all_samples),
        "train_samples": len(train_set),
        "val_samples": len(val_set),
        "language_pairs": final_pair_counts,
        "nllb_lang_mapping": NLLB_MAP,
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"✓ Train File : {train_file} ({train_file.stat().st_size / (1024*1024):.2f} MB)")
    print(f"✓ Val File   : {val_file} ({val_file.stat().st_size / (1024*1024):.2f} MB)")
    print(f"✓ Metadata   : {meta_file}")
    print("Massive inter-local dataset successfully created!")


if __name__ == "__main__":
    build_massive_corpus(target_per_direction=8000, min_score=1.05)
