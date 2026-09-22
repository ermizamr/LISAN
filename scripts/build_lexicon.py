"""
Build data-driven unigram lexicons from HornMT and Bitext corpora.
Used by pyctcdecode for vocabulary-guided CTC beam search decoding.
"""

from collections import Counter
import csv
import os
from pathlib import Path
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
LEXICON_DIR = DATA_DIR / "lexicon"
LEXICON_DIR.mkdir(parents=True, exist_ok=True)

def clean_words(text: str) -> list[str]:
    # Tokenize words, supporting apostrophes (hudhaa in Oromo, e.g. bal'aa)
    tokens = re.findall(r"[^\W\d_]+(?:['’`][^\W\d_]+)*", text, flags=re.UNICODE)
    return [t.strip().lower() for t in tokens if len(t.strip()) > 1]

def build_lexicons():
    counts = {
        "orm": Counter(),
        "amh": Counter(),
        "tir": Counter(),
        "som": Counter(),
    }
    # Track gold vocabulary from HornMT
    gold_vocab = {
        "orm": set(),
        "amh": set(),
        "tir": set(),
        "som": set(),
    }

    # 1. HornMT verified corpora
    hornmt_dir = DATA_DIR / "hornmt"
    for lang in ["orm", "amh", "tir", "som"]:
        fpath = hornmt_dir / f"{lang}.txt"
        if fpath.exists():
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    words = clean_words(line)
                    counts[lang].update(words)
                    gold_vocab[lang].update(words)
            print(f"HornMT {lang}: {len(gold_vocab[lang])} unique gold words")

    # 2. Raw bitext corpora (sample first 50,000 lines per pair for fast build)
    bitext_dir = DATA_DIR / "raw_bitext"
    bitext_files = [
        ("amharic-oromo.csv", "amh", "orm"),
        ("amharic-tigrinya.csv", "amh", "tir"),
        ("amharic-somali.csv", "amh", "som"),
        ("oromo-tigrinya.csv", "orm", "tir"),
    ]

    for fname, src_l, tgt_l in bitext_files:
        fpath = bitext_dir / fname
        if fpath.exists():
            print(f"Reading bitext {fname}...")
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i > 200000:
                        break
                    if len(row) >= 2:
                        counts[src_l].update(clean_words(row[0]))
                        counts[tgt_l].update(clean_words(row[1]))

    # Write out unigrams (union of HornMT gold vocab + frequent bitext words)
    for lang, counter in counts.items():
        out_file = LEXICON_DIR / f"{lang}_unigrams.txt"
        bitext_words = {word for word, count in counter.items() if count >= 2 and len(word) >= 2}
        all_words = sorted(gold_vocab[lang].union(bitext_words))
        with open(out_file, "w", encoding="utf-8") as f:
            for word in all_words:
                f.write(f"{word}\n")
        print(f"✓ Saved {lang} lexicon: {len(all_words)} unigrams -> {out_file}")

if __name__ == "__main__":
    build_lexicons()
