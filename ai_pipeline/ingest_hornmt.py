"""
Automated Ingestion Script for HornMT Benchmark Dataset
======================================================
HornMT (Asmelash Teka et al.) is a multi-way parallel machine translation benchmark
for Horn of Africa languages: Amharic (amh), Afaan Oromo (orm), Somali (som),
Tigrinya (tir), and English (eng).

This script:
1. Downloads and caches HornMT data files and metadata locally in data/hornmt/
2. Validates line alignment across all 5 languages (2,030 lines each)
3. Generates all 20 directed language pairs (2,030 x 20 = 40,600 pairs)
4. Bulk-inserts records into data/translation_memory.db with rich topic domains
"""

from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path
import urllib.request

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ai_pipeline.translation_memory import TranslationMemory

HORNMT_REPO_BASE = "https://raw.githubusercontent.com/asmelashteka/HornMT/main/"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "hornmt"
LANGUAGES = ["amh", "orm", "tir", "som", "eng"]


def download_file(url: str, dest_path: Path) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and dest_path.stat().st_size > 0:
        print(f"  [cached] {dest_path.name} ({dest_path.stat().st_size:,} bytes)")
        return

    print(f"  [downloading] {url} -> {dest_path.name}...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Lisan-Offline-Translator/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read()
    with open(dest_path, "wb") as f:
        f.write(content)
    print(f"  ✓ Saved {dest_path.name} ({len(content):,} bytes)")


def fetch_all_hornmt_files() -> dict[str, list[str]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_by_lang: dict[str, list[str]] = {}

    for lang in LANGUAGES:
        dest = DATA_DIR / f"{lang}.txt"
        url = f"{HORNMT_REPO_BASE}data/{lang}.txt"
        download_file(url, dest)
        with open(dest, "r", encoding="utf-8", errors="replace") as f:
            lines = [line.strip() for line in f]
        data_by_lang[lang] = lines

    meta_dest = DATA_DIR / "metadata.tsv"
    meta_url = f"{HORNMT_REPO_BASE}metadata.tsv"
    download_file(meta_url, meta_dest)

    return data_by_lang


def parse_metadata() -> list[dict]:
    meta_file = DATA_DIR / "metadata.tsv"
    metadata = []
    if not meta_file.exists():
        return metadata

    with open(meta_file, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            metadata.append(row)
    return metadata


def ingest_hornmt(batch_size: int = 5000) -> int:
    print("\n=======================================================")
    print("🚀 Ingesting HornMT Parallel Benchmark into Translation Memory")
    print("=======================================================\n")

    data = fetch_all_hornmt_files()
    metadata = parse_metadata()

    # Validate alignment
    num_sentences = len(data["eng"])
    for lang, lines in data.items():
        if len(lines) != num_sentences:
            raise ValueError(f"Line count mismatch: eng has {num_sentences}, but {lang} has {len(lines)}")

    print(f"\n✓ Verified {num_sentences:,} aligned parallel sentences across {len(LANGUAGES)} languages.")
    if metadata:
        print(f"✓ Loaded {len(metadata):,} metadata rows with category/domain tags.")

    tm = TranslationMemory.get_instance()
    conn = tm._get_connection()

    # Check existing HornMT count
    cur = conn.execute("SELECT COUNT(*) FROM translation_memory WHERE source_dataset = 'hornmt'")
    existing_count = cur.fetchone()[0]
    if existing_count > 0:
        print(f"\n⚠ Found {existing_count:,} existing HornMT entries. Clearing old HornMT entries to re-index...")
        with conn:
            conn.execute("DELETE FROM translation_memory WHERE source_dataset = 'hornmt'")

    records = []
    total_pairs = 0

    print("\nBuilding multi-way parallel translation pairs...")
    for idx in range(num_sentences):
        # Extract topic/category from metadata if present
        domain = "news"
        if idx < len(metadata):
            cat = metadata[idx].get("Category", "").strip().lower()
            if cat:
                domain = cat

        # Generate directed pairs between all distinct language pairs
        for src_lang in LANGUAGES:
            src_text = data[src_lang][idx].strip()
            if not src_text:
                continue

            for tgt_lang in LANGUAGES:
                if src_lang == tgt_lang:
                    continue
                tgt_text = data[tgt_lang][idx].strip()
                if not tgt_text:
                    continue

                records.append({
                    "src_lang": src_lang,
                    "tgt_lang": tgt_lang,
                    "source": src_text,
                    "target": tgt_text,
                    "domain": domain,
                    "dataset": "hornmt",
                    "confidence": 1.0,
                })

                if len(records) >= batch_size:
                    inserted = tm.bulk_insert(records, bidirectional=False)
                    total_pairs += inserted
                    print(f"  Inserted {total_pairs:,} / {num_sentences * len(LANGUAGES) * (len(LANGUAGES)-1):,} pairs...")
                    records.clear()

    if records:
        inserted = tm.bulk_insert(records, bidirectional=False)
        total_pairs += inserted
        records.clear()

    print(f"\n[SUCCESS] Successfully ingested {total_pairs:,} HornMT parallel translation pairs into translation_memory.db!")

    # Verify per-language counts
    cur = conn.execute("""
        SELECT src_lang, tgt_lang, COUNT(*) 
        FROM translation_memory 
        WHERE source_dataset = 'hornmt' 
        GROUP BY src_lang, tgt_lang
    """)
    rows = cur.fetchall()
    print("\nBreakdown of HornMT pairs:")
    for r in rows:
        print(f"  • {r[0]} -> {r[1]}: {r[2]:,} pairs")

    return total_pairs


if __name__ == "__main__":
    ingest_hornmt()
