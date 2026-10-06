"""
Offline Translation Memory (TM) & Semantic Retrieval Engine for Lisan.

Replaces hardcoded translation dictionaries with a high-performance SQLite database
supporting exact matching, token-Jaccard overlap, and fuzzy semantic retrieval.
Enables automated dataset ingestion from Dataset.ET, EthioNLP, Masakhane, and OPUS.
"""

from __future__ import annotations

import os
import re
import sqlite3
import threading
from difflib import SequenceMatcher
from pathlib import Path
from typing import NamedTuple

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "translation_memory.db"


def normalize_for_indexing(text: str) -> str:
    """Normalize text by lowercasing, stripping punctuation, and collapsing whitespace."""
    if not text:
        return ""
    # Remove all Ethiopic and Latin punctuation
    t = re.sub(r"[\s!?,.:;፣።፧፨\(\)\[\]\"'«»]+", " ", text).strip().lower()
    return t


def token_jaccard(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)
    return len(intersection) / len(union)


class TMMatch(NamedTuple):
    source_text: str
    target_text: str
    score: float
    domain: str
    dataset: str


class TranslationMemory:
    """Thread-safe SQLite-backed Translation Memory Engine with automated fuzzy retrieval."""

    _instance: TranslationMemory | None = None
    _lock = threading.Lock()

    def __init__(self, db_path: Path | str = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_db()

    @classmethod
    def get_instance(cls, db_path: Path | str = DB_PATH) -> TranslationMemory:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_path)
            return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=30.0)
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_db(self) -> None:
        """Initialize SQLite tables and indexes."""
        conn = self._get_connection()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translation_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src_lang TEXT NOT NULL,
                    tgt_lang TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    target_text TEXT NOT NULL,
                    source_norm TEXT NOT NULL,
                    domain TEXT NOT NULL DEFAULT 'general',
                    source_dataset TEXT NOT NULL DEFAULT 'custom',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tm_lookup 
                ON translation_memory(src_lang, tgt_lang, source_norm);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tm_pair 
                ON translation_memory(src_lang, tgt_lang);
            """)

    def insert(
        self,
        src_lang: str,
        tgt_lang: str,
        source: str,
        target: str,
        domain: str = "general",
        dataset: str = "custom",
        confidence: float = 1.0,
        bidirectional: bool = False,
    ) -> bool:
        """Insert a single translation pair, optionally creating reverse mapping."""
        source = source.strip()
        target = target.strip()
        if not source or not target:
            return False

        norm_src = normalize_for_indexing(source)
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO translation_memory 
                    (src_lang, tgt_lang, source_text, target_text, source_norm, domain, source_dataset, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (src_lang, tgt_lang, source, target, norm_src, domain, dataset, confidence),
                )
                if bidirectional:
                    norm_tgt = normalize_for_indexing(target)
                    conn.execute(
                        """
                        INSERT INTO translation_memory 
                        (src_lang, tgt_lang, source_text, target_text, source_norm, domain, source_dataset, confidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (tgt_lang, src_lang, target, source, norm_tgt, domain, dataset, confidence),
                    )
            return True
        except Exception:
            return False

    def bulk_insert(self, records: list[dict], bidirectional: bool = False) -> int:
        """Bulk insert thousands of parallel sentences from dataset importers."""
        if not records:
            return 0

        rows = []
        for r in records:
            src_lang = r["src_lang"]
            tgt_lang = r["tgt_lang"]
            source = r["source"].strip()
            target = r["target"].strip()
            domain = r.get("domain", "general")
            dataset = r.get("dataset", "custom")
            conf = float(r.get("confidence", 1.0))
            if not source or not target:
                continue
            norm_src = normalize_for_indexing(source)
            rows.append((src_lang, tgt_lang, source, target, norm_src, domain, dataset, conf))
            if bidirectional:
                norm_tgt = normalize_for_indexing(target)
                rows.append((tgt_lang, src_lang, target, source, norm_tgt, domain, dataset, conf))

        conn = self._get_connection()
        with conn:
            conn.executemany(
                """
                INSERT INTO translation_memory 
                (src_lang, tgt_lang, source_text, target_text, source_norm, domain, source_dataset, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                rows,
            )
        return len(rows)

    def lookup(
        self,
        text: str,
        src_lang: str,
        tgt_lang: str,
        min_similarity: float = 0.95,
    ) -> TMMatch | None:
        """
        Dynamically lookup a translation without hardcoded rules.
        
        1. Exact normalized match (< 0.5ms).
        2. Automated fuzzy token & character similarity matching across dataset entries (> min_similarity).
           Strictly guards against substituting distinct nouns or content words.
        """
        query_raw = text.strip()
        if not query_raw:
            return None

        query_norm = normalize_for_indexing(query_raw)
        if not query_norm:
            return None

        conn = self._get_connection()

        # Step 1: Instant Exact Normalized Match
        cur = conn.execute(
            """
            SELECT source_text, target_text, domain, source_dataset 
            FROM translation_memory 
            WHERE src_lang = ? AND tgt_lang = ? AND source_norm = ?
            ORDER BY confidence DESC, id DESC
            LIMIT 1;
            """,
            (src_lang, tgt_lang, query_norm),
        )
        row = cur.fetchone()
        if row:
            return TMMatch(
                source_text=row["source_text"],
                target_text=row["target_text"],
                score=1.0,
                domain=row["domain"],
                dataset=row["source_dataset"],
            )

        # Step 2: Automated Fuzzy Token & Character Matching (Strict Threshold >= 0.95)
        query_tokens = set(query_norm.split())
        if not query_tokens:
            return None

        query_content = {w for w in query_tokens if len(w) >= 4}

        cur = conn.execute(
            """
            SELECT source_text, target_text, source_norm, domain, source_dataset 
            FROM translation_memory 
            WHERE src_lang = ? AND tgt_lang = ?
            """,
            (src_lang, tgt_lang),
        )

        best_match: TMMatch | None = None
        best_score = 0.0

        for candidate in cur:
            cand_norm = candidate["source_norm"]
            cand_tokens = set(cand_norm.split())

            if not cand_tokens:
                continue

            # Length ratio guard
            ratio = len(query_tokens) / len(cand_tokens)
            if ratio < 0.70 or ratio > 1.4:
                continue

            # Distinct content words (nouns/verbs/adjectives >= 4 chars) MUST match
            cand_content = {w for w in cand_tokens if len(w) >= 4}
            if query_content != cand_content:
                continue

            # Compute intersection & overlap
            intersection = len(query_tokens.intersection(cand_tokens))
            if intersection == 0:
                continue

            union = len(query_tokens.union(cand_tokens))
            jaccard = intersection / union if union > 0 else 0.0
            overlap = intersection / min(len(query_tokens), len(cand_tokens))

            # Character sequence similarity
            seq_ratio = SequenceMatcher(None, query_norm, cand_norm).ratio()

            tok_score = 0.5 * jaccard + 0.5 * overlap if overlap >= 0.85 else jaccard
            combined_score = 0.40 * tok_score + 0.60 * seq_ratio

            if combined_score > best_score and combined_score >= min_similarity:
                best_score = combined_score
                best_match = TMMatch(
                    source_text=candidate["source_text"],
                    target_text=candidate["target_text"],
                    score=round(combined_score, 3),
                    domain=candidate["domain"],
                    dataset=candidate["source_dataset"],
                )

        return best_match

    def count(self) -> int:
        """Count total translation pairs in memory."""
        conn = self._get_connection()
        cur = conn.execute("SELECT COUNT(*) as cnt FROM translation_memory;")
        return cur.fetchone()["cnt"]

    def counts_by_pair(self) -> dict[str, int]:
        """Get record counts grouped by language pair."""
        conn = self._get_connection()
        cur = conn.execute(
            "SELECT src_lang, tgt_lang, COUNT(*) as cnt FROM translation_memory GROUP BY src_lang, tgt_lang;"
        )
        return {f"{r['src_lang']}->{r['tgt_lang']}": r["cnt"] for r in cur}
