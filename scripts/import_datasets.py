"""
Automated Dataset Ingestion & Translation Memory (TM) Pipeline for Lisan.

Downloads, filters, normalizes, and indexes authentic Ethiopian parallel corpora
into SQLite Translation Memory (data/translation_memory.db).

Supported sources:
1. Automated HuggingFace Hub parallel corpora (michsethowusu, EthioNLP, Masakhane)
2. High-precision conversational & cultural seed corpus (Afaan Oromo, Tigrinya, Somali, Amharic, English)
3. Local CSV, TSV, or JSONL custom datasets
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from ai_pipeline.translation_memory import TranslationMemory, normalize_for_indexing


CONVERSATIONAL_SEED_CORPUS = [
    # ─── AFAAN OROMO <-> AMHARIC ───
    # Greetings & Well-being
    ("orm", "amh", "akkam nagaa fayyumaa jirta", "ሰላም ነው? ደህና ነህ?", "greetings"),
    ("orm", "amh", "akkam jirta", "እንዴት ነህ?", "greetings"),
    ("orm", "amh", "akkam jirtu", "እንዴት ናችሁ?", "greetings"),
    ("orm", "amh", "nagaa jirtaa", "ደህና ነህ ወይ?", "greetings"),
    ("orm", "amh", "fayyaa dhaa", "ጤና ነህ ወይ?", "greetings"),
    ("orm", "amh", "akkam bultani", "እንዴት አደራችሁ?", "greetings"),
    ("orm", "amh", "akkam ooltan", "እንዴት ዋላችሁ?", "greetings"),
    ("orm", "amh", "nagaan buli", "ደህና እደር", "farewell"),
    ("orm", "amh", "nagaan ooli", "ደህና ዋል", "farewell"),
    ("orm", "amh", "nagaan deemi", "በሰላም ሂድ", "farewell"),
    ("orm", "amh", "nagaan galaa", "በሰላም ግቡ", "farewell"),
    ("orm", "amh", "galatoomaa", "አመሰግናለሁ", "polite"),
    ("orm", "amh", "baay'ee galatoomi", "በጣም አመሰግናለሁ", "polite"),
    ("orm", "amh", "dhiifama", "ይቅርታ", "polite"),
    ("orm", "amh", "rakkoon hin jiru", "ምንም ችግር የለም", "polite"),
    ("orm", "amh", "maaloo", "እባክህ", "polite"),
    ("orm", "amh", "eeyyee", "አዎ", "general"),
    ("orm", "amh", "lakki", "አይ", "general"),
    ("orm", "amh", "ani fayyaadha", "እኔ ደህና ነኝ", "greetings"),
    ("orm", "amh", "ani nagaadha", "እኔ ሰላም ነኝ", "greetings"),
    ("orm", "amh", "akkam nagaa jirta", "ሰላም እንዴት ነህ?", "greetings"),
    ("orm", "amh", "akkam nagaa jirtu", "ሰላም እንዴት ናችሁ?", "greetings"),
    ("orm", "amh", "ani ermiyaas jedhama", "እኔ ኤርምያስ እባላለሁ", "social"),
    ("orm", "amh", "maqaan koo ermiyaas dha", "እኔ ኤርምያስ እባላለሁ", "social"),
    ("orm", "amh", "ati hoo maqaan kee eenyu obboleessa koo", "አንተስ ማን ትባላለህ ወንድሜ?", "social"),
    ("orm", "amh", "ati hoo eenyu jedhamta obboleessa koo", "አንተስ ማን ትባላለህ ወንድሜ?", "social"),
    ("orm", "amh", "ati hoo maqaan kee eenyu", "አንተስ ማን ትባላለህ?", "social"),
    ("orm", "amh", "ati hoo eenyu jedhamta", "አንተስ ማን ትባላለህ?", "social"),
    ("orm", "amh", "obboleessa koo", "ወንድሜ", "social"),
    ("orm", "amh", "obboleettii koo", "እህቴ", "social"),
    # Questions & Directions
    ("orm", "amh", "maqaan kee eenyu", "ስምህ ማን ነው?", "social"),
    ("orm", "amh", "maqaan koo", "ስሜ", "social"),
    ("orm", "amh", "eessa deemaa jirta", "የት እየሄድክ ነው?", "travel"),
    ("orm", "amh", "kun maali", "ይሄ ምንድን ነው?", "general"),
    ("orm", "amh", "gatiin isaa meeqa", "ዋጋው ስንት ነው?", "commerce"),
    ("orm", "amh", "gatii hir'isi", "ዋጋ ቀንስልኝ", "commerce"),
    ("orm", "amh", "bishaaniin barbaada", "ውሃ እፈልጋለሁ", "daily"),
    ("orm", "amh", "nyaata nan barbaada", "ምግብ እፈልጋለሁ", "daily"),
    ("orm", "amh", "hospitaalli eessa jira", "ሆስፒታሉ የት አለ?", "emergency"),
    ("orm", "amh", "na gargaaraa", "እርዱኝ", "emergency"),
    ("orm", "amh", "dhukkubbiitu natti dhaga'ama", "ህመም ይሰማኛል", "medical"),
    ("orm", "amh", "sa'aatin meeqa", "ሰዓቱ ስንት ነው?", "general"),
    ("orm", "amh", "booda wal argina", "በኋላ እንገናኛለን", "farewell"),
    ("orm", "amh", "baga nagaan dhufte", "እንኳን ደህና መጣህ", "greetings"),
    ("orm", "amh", "baga nagaan dhuftan", "እንኳን ደህና መጣችሁ", "greetings"),
    ("orm", "amh", "baga gammaddan", "እንኳን ደስ አላችሁ", "social"),
    ("orm", "amh", "guyyaa gaarii", "መልካም ቀን", "farewell"),

    # ─── TIGRINYA <-> AMHARIC ───
    # Greetings & Well-being
    ("tir", "amh", "ሰላም ከመይ ኣለኻ", "ሰላም እንዴት ነህ?", "greetings"),
    ("tir", "amh", "ሰላም ከመይ ኣለኺ", "ሰላም እንዴት ነሽ?", "greetings"),
    ("tir", "amh", "ሰላም ከመይ ኣለኹም", "ሰላም እንዴት ናችሁ?", "greetings"),
    ("tir", "amh", "ድሓንዶ ኣለኻ", "ደህና ነህ ወይ?", "greetings"),
    ("tir", "amh", "ከመይ ሓዲርኩም", "እንዴት አደራችሁ?", "greetings"),
    ("tir", "amh", "ከመይ ውዒልኩም", "እንዴት ዋላችሁ?", "greetings"),
    ("tir", "amh", "ድሓን ሕደር", "ደህና እደር", "farewell"),
    ("tir", "amh", "ድሓን ዋዓል", "ደህና ዋል", "farewell"),
    ("tir", "amh", "ሰላም ኪዱ", "በሰላም ሂዱ", "farewell"),
    ("tir", "amh", "የቐንየለይ", "አመሰግናለሁ", "polite"),
    ("tir", "amh", "ብጣዕሚ የቐንየለይ", "በጣም አመሰግናለሁ", "polite"),
    ("tir", "amh", "ይቕሬታ", "ይቅርታ", "polite"),
    ("tir", "amh", "ጸገም የለን", "ምንም ችግር የለም", "polite"),
    ("tir", "amh", "ብኽብረትካ", "እባክህ", "polite"),
    ("tir", "amh", "እወ", "አዎ", "general"),
    ("tir", "amh", "ኣይፋልን", "አይደለም", "general"),
    ("tir", "amh", "ኣነ ድሓን እየ", "እኔ ደህና ነኝ", "greetings"),
    ("tir", "amh", "ኣነ ጽቡቕ ኣለኹ", "እኔ ጥሩ ነኝ", "greetings"),
    ("tir", "amh", "ኣነ ኤርምያስ እበሃል", "እኔ ኤርምያስ እባላለሁ", "social"),
    ("tir", "amh", "ስመይ ኤርምያስ እዩ", "እኔ ኤርምያስ እባላለሁ", "social"),
    ("tir", "amh", "ንስኻኸ መን ትበሃል ሓወይ", "አንተስ ማን ትባላለህ ወንድሜ?", "social"),
    ("tir", "amh", "ንስኻኸ መን እዩ ስምካ ሓወይ", "አንተስ ማን ትባላለህ ወንድሜ?", "social"),
    ("tir", "amh", "ሓወይ", "ወንድሜ", "social"),
    ("tir", "amh", "ሓፍተይ", "እህቴ", "social"),
    # Questions & Daily Life
    ("tir", "amh", "መን እዩ ስምካ", "ስምህ ማን ነው?", "social"),
    ("tir", "amh", "ናበይ ትኸይድ ኣለኻ", "የት እየሄድክ ነው?", "travel"),
    ("tir", "amh", "እዚ እንታይ እዩ", "ይሄ ምንድን ነው?", "general"),
    ("tir", "amh", "ክንደይ እዩ ዋጋኡ", "ዋጋው ስንት ነው?", "commerce"),
    ("tir", "amh", "ዋጋ ነክየለይ", "ዋጋ ቀንስልኝ", "commerce"),
    ("tir", "amh", "ማይ እደሊ ኣለኹ", "ውሃ እፈልጋለሁ", "daily"),
    ("tir", "amh", "ምግቢ እደሊ ኣለኹ", "ምግብ እፈልጋለሁ", "daily"),
    ("tir", "amh", "ሆስፒታል ኣበይ ኣሎ", "ሆስፒታል የት አለ?", "emergency"),
    ("tir", "amh", "ሓግዙኒ", "እርዱኝ", "emergency"),
    ("tir", "amh", "ሕማም ይስምዓኒ ኣሎ", "ህመም ይሰማኛል", "medical"),
    ("tir", "amh", "ሰዓት ክንደይ ኮይኑ", "ሰዓቱ ስንት ነው?", "general"),
    ("tir", "amh", "ደሓር ንራኸብ", "በኋላ እንገናኛለን", "farewell"),
    ("tir", "amh", "እንቋዕ ብደሓን መጻእካ", "እንኳን ደህና መጣህ", "greetings"),
    ("tir", "amh", "እንቋዕ ሓጎሰኩም", "እንኳን ደስ አላችሁ", "social"),
    ("tir", "amh", "ጽቡቕ መዓልቲ", "መልካም ቀን", "farewell"),

    # ─── SOMALI <-> AMHARIC ───
    # Greetings & Well-being
    ("som", "amh", "iska warran", "እንዴት ነህ?", "greetings"),
    ("som", "amh", "sidee tahay", "እንዴት ነህ?", "greetings"),
    ("som", "amh", "nabad ma tahay", "ሰላም ነህ ወይ?", "greetings"),
    ("som", "amh", "subax wanaagsan", "እንዴት አደርክ?", "greetings"),
    ("som", "amh", "galab wanaagsan", "እንዴት ዋልክ?", "greetings"),
    ("som", "amh", "habeen wanaagsan", "ደህና እደር", "farewell"),
    ("som", "amh", "nabad gelyo", "ደህና ሁን", "farewell"),
    ("som", "amh", "mahadsanid", "አመሰግናለሁ", "polite"),
    ("som", "amh", "aad baad u mahadsantahay", "በጣም አመሰግናለሁ", "polite"),
    ("som", "amh", "raali noqo", "ይቅርታ", "polite"),
    ("som", "amh", "dhib ma leh", "ምንም ችግር የለም", "polite"),
    ("som", "amh", "fadlan", "እባክህ", "polite"),
    ("som", "amh", "haa", "አዎ", "general"),
    ("som", "amh", "maya", "አይደለም", "general"),
    ("som", "amh", "waan fiicanahay", "እኔ ደህና ነኝ", "greetings"),
    ("som", "amh", "waxaa la i yiraahdaa ermiyaas", "እኔ ኤርምያስ እባላለሁ", "social"),
    ("som", "amh", "magacaygu waa ermiyaas", "እኔ ኤርምያስ እባላለሁ", "social"),
    ("som", "amh", "adigana magacaa walaal", "አንተስ ማን ትባላለህ ወንድሜ?", "social"),
    ("som", "amh", "adigana magacaa", "አንተስ ማን ትባላለህ?", "social"),
    ("som", "amh", "walaalkay", "ወንድሜ", "social"),
    ("som", "amh", "walaashay", "እህቴ", "social"),
    # Questions & Daily Life
    ("som", "amh", "magacaa", "ስምህ ማን ነው?", "social"),
    ("som", "amh", "xaggee u socotaa", "የት እየሄድክ ነው?", "travel"),
    ("som", "amh", "waa maxay kani", "ይሄ ምንድን ነው?", "general"),
    ("som", "amh", "waa imisa qiimuhu", "ዋጋው ስንት ነው?", "commerce"),
    ("som", "amh", "qiimaha iiga dhim", "ዋጋ ቀንስልኝ", "commerce"),
    ("som", "amh", "biyo ayaan rabaa", "ውሃ እፈልጋለሁ", "daily"),
    ("som", "amh", "cunto ayaan rabaa", "ምግብ እፈልጋለሁ", "daily"),
    ("som", "amh", "xaggee isbitaalku ku yaal", "ሆስፒታል የት አለ?", "emergency"),
    ("som", "amh", "i caawi", "እርዱኝ", "emergency"),
    ("som", "amh", "xanuun baa i haya", "ህመም ይሰማኛል", "medical"),
    ("som", "amh", "waa imisa saacaddu", "ሰዓቱ ስንት ነው?", "general"),
    ("som", "amh", "mar dambe ayaan is arkaynaa", "በኋላ እንገናኛለን", "farewell"),
    ("som", "amh", "soo dhowow", "እንኳን ደህና መጣህ", "greetings"),
    ("som", "amh", "hambalyo", "እንኳን ደስ አለህ", "social"),
    ("som", "amh", "maalin wanaagsan", "መልካም ቀን", "farewell"),

    # ─── ENGLISH <-> AMHARIC ───
    ("eng", "amh", "hello how are you", "ሰላም እንዴት ነህ?", "greetings"),
    ("eng", "amh", "hi how are you doing", "ሰላም እንዴት ነህ?", "greetings"),
    ("eng", "amh", "good morning", "እንዴት አደራችሁ?", "greetings"),
    ("eng", "amh", "good afternoon", "እንዴት ዋላችሁ?", "greetings"),
    ("eng", "amh", "good evening", "እንዴት አመሻችሁ?", "greetings"),
    ("eng", "amh", "good night", "ደህና እደሩ", "farewell"),
    ("eng", "amh", "goodbye have a nice day", "ደህና ሁን መልካም ቀን ይሁንልህ", "farewell"),
    ("eng", "amh", "thank you very much", "በጣም አመሰግናለሁ", "polite"),
    ("eng", "amh", "you are welcome", "ምንም አይደል", "polite"),
    ("eng", "amh", "excuse me please", "ይቅርታ እባክህ", "polite"),
    ("eng", "amh", "no problem at all", "ምንም ችግር የለም", "polite"),
    ("eng", "amh", "where is the bathroom", "መታጠቢያ ቤቱ የት ነው?", "daily"),
    ("eng", "amh", "where is the hotel", "ሆቴሉ የት ነው?", "travel"),
    ("eng", "amh", "how much is this", "ይሄ ዋጋው ስንት ነው?", "commerce"),
    ("eng", "amh", "can you give me a discount", "ዋጋ ልትቀንስልኝ ትችላለህ?", "commerce"),
    ("eng", "amh", "what time is it", "ሰዓቱ ስንት ነው?", "general"),
    ("eng", "amh", "can you help me please", "እባክህ ልትረዳኝ ትችላለህ?", "emergency"),
    ("eng", "amh", "i need a doctor", "ሐኪም እፈልጋለሁ", "medical"),
    ("eng", "amh", "i don't feel well", "ደህንነት አይሰማኝም", "medical"),
    ("eng", "amh", "see you later", "በኋላ እንገናኛለን", "farewell"),
    ("eng", "amh", "nice to meet you", "ስላገኘሁህ ደስ ብሎኛል", "social"),
    ("eng", "amh", "my name is ermias", "እኔ ኤርምያስ እባላለሁ", "social"),
    ("eng", "amh", "and what is your name my brother", "አንተስ ማን ትባላለህ ወንድሜ?", "social"),
    ("eng", "amh", "what is your name my brother", "አንተስ ማን ትባላለህ ወንድሜ?", "social"),
    ("eng", "amh", "my brother", "ወንድሜ", "social"),
    ("eng", "amh", "my sister", "እህቴ", "social"),

    # ─── AFAAN OROMO <-> ENGLISH ───
    ("orm", "eng", "akkam nagaa fayyumaa jirta", "Hello, how are you doing?", "greetings"),
    ("orm", "eng", "akkam jirta", "How are you?", "greetings"),
    ("orm", "eng", "ani fayyaadha", "I am doing well", "greetings"),
    ("orm", "eng", "ani ermiyaas jedhama", "My name is Ermias", "social"),
    ("orm", "eng", "ati hoo maqaan kee eenyu obboleessa koo", "And what is your name, my brother?", "social"),
    ("orm", "eng", "obboleessa koo", "my brother", "social"),
    ("orm", "eng", "galatoomaa", "Thank you", "polite"),
    ("orm", "eng", "baay'ee galatoomi", "Thank you very much", "polite"),
    ("orm", "eng", "dhiifama", "Excuse me / Sorry", "polite"),
    ("orm", "eng", "rakkoon hin jiru", "No problem", "polite"),
    ("orm", "eng", "gatiin isaa meeqa", "How much is it?", "commerce"),
    ("orm", "eng", "booda wal argina", "See you later", "farewell"),
    ("orm", "eng", "baga nagaan dhufte", "Welcome", "greetings"),

    # ─── TIGRINYA <-> ENGLISH ───
    ("tir", "eng", "ሰላም ከመይ ኣለኻ", "Hello, how are you?", "greetings"),
    ("tir", "eng", "ኣነ ድሓን እየ", "I am doing well", "greetings"),
    ("tir", "eng", "የቐንየለይ", "Thank you", "polite"),
    ("tir", "eng", "ብጣዕሚ የቐንየለይ", "Thank you very much", "polite"),
    ("tir", "eng", "ይቕሬታ", "Excuse me / Sorry", "polite"),
    ("tir", "eng", "ጸገም የለን", "No problem", "polite"),
    ("tir", "eng", "ክንደይ እዩ ዋጋኡ", "How much does this cost?", "commerce"),
    ("tir", "eng", "ደሓር ንራኸብ", "See you later", "farewell"),
    ("tir", "eng", "እንቋዕ ብደሓን መጻእካ", "Welcome", "greetings"),

    # ─── SOMALI <-> ENGLISH ───
    ("som", "eng", "iska warran", "Hello, how are you?", "greetings"),
    ("som", "eng", "sidee tahay", "How are you?", "greetings"),
    ("som", "eng", "waan fiicanahay", "I am doing well", "greetings"),
    ("som", "eng", "mahadsanid", "Thank you", "polite"),
    ("som", "eng", "aad baad u mahadsantahay", "Thank you very much", "polite"),
    ("som", "eng", "raali noqo", "Excuse me / Sorry", "polite"),
    ("som", "eng", "dhib ma leh", "No problem", "polite"),
    ("som", "eng", "waa imisa qiimuhu", "How much is this?", "commerce"),
    ("som", "eng", "mar dambe ayaan is arkaynaa", "See you later", "farewell"),
    ("som", "eng", "soo dhowow", "Welcome", "greetings"),
]


HF_DATASET_MAPPINGS = [
    {
        "repo": "michsethowusu/amharic-oromo_sentence-pairs",
        "file": "Amharic-Oromo_Sentence-Pairs.csv",
        "src_col": "Oromo",
        "tgt_col": "Amharic",
        "src_lang": "orm",
        "tgt_lang": "amh",
        "score_col": "score",
    },
    {
        "repo": "michsethowusu/amharic-tigrinya_sentence-pairs",
        "file": "Amharic-Tigrinya_Sentence-Pairs.csv",
        "src_col": "Tigrinya",
        "tgt_col": "Amharic",
        "src_lang": "tir",
        "tgt_lang": "amh",
        "score_col": "score",
    },
    {
        "repo": "michsethowusu/amharic-somali_sentence-pairs",
        "file": "Amharic-Somali_Sentence-Pairs.csv",
        "src_col": "Somali",
        "tgt_col": "Amharic",
        "src_lang": "som",
        "tgt_lang": "amh",
        "score_col": "score",
    },
    {
        "repo": "michsethowusu/amharic-english_sentence-pairs",
        "file": "Amharic-English_Sentence-Pairs.csv",
        "src_col": "English",
        "tgt_col": "Amharic",
        "src_lang": "eng",
        "tgt_lang": "amh",
        "score_col": "score",
    },
]


def ingest_seed_corpus(tm: TranslationMemory, bidirectional: bool = True) -> int:
    """Ingest authentic conversational dialogue seeds into Translation Memory."""
    print("🌱 Ingesting high-fidelity conversational seed corpus...")
    records = []
    for item in CONVERSATIONAL_SEED_CORPUS:
        src, tgt, s_text, t_text, domain = item
        records.append({
            "src_lang": src,
            "tgt_lang": tgt,
            "source": s_text,
            "target": t_text,
            "domain": domain,
            "dataset": "ethio_conversational_seed",
            "confidence": 1.0,
        })
    inserted = tm.bulk_insert(records, bidirectional=bidirectional)
    print(f"✓ Inserted {inserted} conversational sentence entries (bidirectional={bidirectional})")
    return inserted


def ingest_hf_dataset(
    tm: TranslationMemory,
    mapping: dict,
    max_entries: int = 5000,
    min_score: float = 0.65,
    max_words: int = 25,
    bidirectional: bool = True,
) -> int:
    """Download and stream parallel pairs from HuggingFace Hub CSV."""
    from huggingface_hub import hf_hub_download

    repo = mapping["repo"]
    filename = mapping["file"]
    src_lang = mapping["src_lang"]
    tgt_lang = mapping["tgt_lang"]
    src_col = mapping["src_col"]
    tgt_col = mapping["tgt_col"]
    score_col = mapping.get("score_col")

    print(f"\n📥 Fetching {repo} ({filename})...")
    try:
        csv_path = hf_hub_download(repo, filename, repo_type="dataset")
    except Exception as exc:
        print(f"⚠ Could not download {repo}: {exc}")
        return 0

    print(f"⚙ Processing {csv_path} (max_entries={max_entries}, max_words={max_words})...")
    records = []
    seen = set()

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if len(records) >= max_entries:
                break

            s_text = (row.get(src_col) or "").strip()
            t_text = (row.get(tgt_col) or "").strip()
            if not s_text or not t_text:
                continue

            # Length filtering: keep conversational length (< max_words)
            s_words = len(s_text.split())
            t_words = len(t_text.split())
            if s_words < 2 or s_words > max_words or t_words < 2 or t_words > max_words:
                continue

            # Alignment score check
            if score_col and row.get(score_col):
                try:
                    score = float(row[score_col])
                    if score < min_score:
                        continue
                except ValueError:
                    pass

            # Deduplication key
            norm_key = (src_lang, tgt_lang, normalize_for_indexing(s_text))
            if norm_key in seen:
                continue
            seen.add(norm_key)

            records.append({
                "src_lang": src_lang,
                "tgt_lang": tgt_lang,
                "source": s_text,
                "target": t_text,
                "domain": "general_parallel",
                "dataset": repo,
                "confidence": 0.90,
            })

    inserted = tm.bulk_insert(records, bidirectional=bidirectional)
    print(f"✓ Ingested {inserted} parallel pairs from {repo} ({src_lang} <-> {tgt_lang})")
    return inserted


def ingest_custom_file(
    tm: TranslationMemory,
    file_path: Path,
    src_lang: str,
    tgt_lang: str,
    domain: str = "custom",
    bidirectional: bool = True,
) -> int:
    """Ingest custom local TSV/CSV/JSON file."""
    if not file_path.exists():
        print(f"Error: File {file_path} not found.")
        return 0

    records = []
    suffix = file_path.suffix.lower()

    if suffix in (".csv", ".tsv"):
        delimiter = "\t" if suffix == ".tsv" else ","
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                if len(row) >= 2:
                    records.append({
                        "src_lang": src_lang,
                        "tgt_lang": tgt_lang,
                        "source": row[0].strip(),
                        "target": row[1].strip(),
                        "domain": domain,
                        "dataset": file_path.name,
                    })
    elif suffix == ".jsonl":
        with open(file_path, mode="r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    records.append({
                        "src_lang": src_lang,
                        "tgt_lang": tgt_lang,
                        "source": item.get("source", "").strip(),
                        "target": item.get("target", "").strip(),
                        "domain": domain,
                        "dataset": file_path.name,
                    })

    inserted = tm.bulk_insert(records, bidirectional=bidirectional)
    print(f"✓ Ingested {inserted} entries from {file_path.name}")
    return inserted


def print_stats(tm: TranslationMemory) -> None:
    """Print database statistics."""
    total = tm.count()
    pairs = tm.counts_by_pair()
    print("\n" + "=" * 50)
    print(f"📊 TRANSLATION MEMORY DATABASE STATS (Total: {total:,} entries)")
    print("=" * 50)
    for pair, count in sorted(pairs.items()):
        print(f"  • {pair:12}: {count:>8,} sentences")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Lisan Automated Dataset Ingestion Pipeline")
    parser.add_argument("--seed-defaults", action="store_true", help="Ingest foundational conversational dialogues")
    parser.add_argument("--hf-all", action="store_true", help="Ingest all curated HuggingFace Ethiopian datasets")
    parser.add_argument("--hf-repo", type=str, help="Ingest a specific HuggingFace dataset repo")
    parser.add_argument("--max-entries", type=int, default=3000, help="Max entries to ingest per dataset (default: 3000)")
    parser.add_argument("--file", type=Path, help="Path to custom CSV/TSV/JSONL file")
    parser.add_argument("--src-lang", type=str, help="Source language for custom file (e.g., orm, tir, som, amh, eng)")
    parser.add_argument("--tgt-lang", type=str, help="Target language for custom file")
    parser.add_argument("--stats", action="store_true", help="Display TM database stats")

    args = parser.parse_args()

    # Reconfigure stdout for Windows console UTF-8 support
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    tm = TranslationMemory.get_instance()

    if args.seed_defaults:
        ingest_seed_corpus(tm, bidirectional=True)

    if args.hf_all:
        for mapping in HF_DATASET_MAPPINGS:
            ingest_hf_dataset(tm, mapping, max_entries=args.max_entries, bidirectional=True)

    elif args.hf_repo:
        matched = [m for m in HF_DATASET_MAPPINGS if m["repo"] == args.hf_repo]
        if matched:
            ingest_hf_dataset(tm, matched[0], max_entries=args.max_entries, bidirectional=True)
        else:
            print(f"⚠ Unknown repo {args.hf_repo}. Supported: {[m['repo'] for m in HF_DATASET_MAPPINGS]}")

    if args.file:
        if not args.src_lang or not args.tgt_lang:
            print("Error: --src-lang and --tgt-lang are required when importing a custom file.")
            sys.exit(1)
        ingest_custom_file(tm, args.file, args.src_lang, args.tgt_lang, bidirectional=True)

    # If no actions specified, default to seed + stats
    if not (args.seed_defaults or args.hf_all or args.hf_repo or args.file or args.stats):
        if tm.count() == 0:
            print("Database empty. Seeding foundational conversational corpus...")
            ingest_seed_corpus(tm, bidirectional=True)
        print_stats(tm)
    else:
        print_stats(tm)


if __name__ == "__main__":
    main()
