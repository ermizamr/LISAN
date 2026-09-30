"""
Ingest Dataset.ET Afaan Oromoo Speech v0.1.0 Prompt Text
=========================================================
Downloads metadata.csv from snapwre/afaan-oromoo-speech,
extracts all verified Qubee sentences, normalizes hudhaa (glottal stops),
and enriches data/lexicon/orm_unigrams.txt with authentic spoken vocabulary.
"""

from collections import Counter
import csv
import io
from pathlib import Path
import re
import sys
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
LEXICON_PATH = ROOT_DIR / "data" / "lexicon" / "orm_unigrams.txt"
METADATA_URL = "https://huggingface.co/datasets/snapwre/afaan-oromoo-speech/raw/main/metadata.csv"

def normalize_hudhaa(text: str) -> str:
    """Normalize curved/unicode quotes to ASCII single quote (hudhaa)."""
    return re.sub(r"[’‘`´ʻʼ]", "'", text)

def clean_qubee_words(text: str) -> list[str]:
    """Tokenize Qubee words preserving valid hudhaa glottal stops."""
    text = normalize_hudhaa(text)
    # Match words composed of letters, with internal apostrophes (e.g. bal'aa, ba'uu)
    tokens = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)*\b", text)
    cleaned = []
    for t in tokens:
        word = t.strip().lower()
        # Filter noise or single non-meaningful characters (except valid 1-char particles if any)
        if len(word) >= 2 and not word.isdigit():
            cleaned.append(word)
    return cleaned

def ingest_dataset_et_oromo():
    print(f"Fetching Dataset.ET Afaan Oromoo metadata from {METADATA_URL}...")
    try:
        req = urllib.request.Request(
            METADATA_URL,
            headers={"User-Agent": "Lisan-Offline-Translator/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return

    reader = csv.DictReader(io.StringIO(content))
    word_counter = Counter()
    sentence_count = 0

    for row in reader:
        sentence = row.get("sentence", "").strip()
        if sentence:
            sentence_count += 1
            words = clean_qubee_words(sentence)
            word_counter.update(words)

    print(f"Parsed {sentence_count} prompt sentences from Dataset.ET.")
    print(f"Extracted {len(word_counter)} unique Qubee words.")

    # Read existing lexicon if available
    existing_words = set()
    if LEXICON_PATH.exists():
        for line in LEXICON_PATH.read_text(encoding="utf-8").splitlines():
            line_clean = normalize_hudhaa(line.strip().lower())
            if line_clean and len(line_clean) >= 2:
                existing_words.add(line_clean)
        print(f"Existing Oromo lexicon: {len(existing_words)} words.")

    # Union with newly extracted Dataset.ET words
    dataset_et_words = set(word_counter.keys())
    combined_words = sorted(existing_words.union(dataset_et_words))

    # Write back enriched lexicon
    LEXICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LEXICON_PATH, "w", encoding="utf-8") as f:
        for w in combined_words:
            f.write(f"{w}\n")

    added_count = len(combined_words) - len(existing_words)
    print(f"✓ Saved updated Oromo lexicon: {len(combined_words)} words ({added_count} new from Dataset.ET) -> {LEXICON_PATH}")

if __name__ == "__main__":
    ingest_dataset_et_oromo()
