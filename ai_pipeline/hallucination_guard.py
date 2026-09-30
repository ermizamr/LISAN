"""
Hallucination & Degeneration Guard for Ethiopian Multilingual NLP.

Protects against:
1. Length-ratio drift (e.g., 3-word input becoming a 20-word hallucinated essay).
2. Cyclic n-gram repetition loops (common NLLB/seq2seq attention collapse).
3. Subject/Entity loss during neural pivot.
4. Provides calibrated confidence scoring and warning hints for UI display.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import NamedTuple


@dataclass
class GuardResult:
    confidence: float
    is_tm_hit: bool
    is_uncertain: bool
    warning: str | None
    clean_translation: str


class HallucinationGuard:
    """
    Evaluates translation output sanity and catches neural generation anomalies.
    """

    @classmethod
    def detect_repetition(cls, text: str) -> bool:
        """Detect cyclic repetition of words or phrases."""
        words = text.strip().split()
        if len(words) < 6:
            return False

        # Check consecutive duplicate words (3+ times)
        repeat_word_count = 0
        for i in range(1, len(words)):
            if words[i].lower() == words[i - 1].lower():
                repeat_word_count += 1
                if repeat_word_count >= 2:
                    return True
            else:
                repeat_word_count = 0

        # Check consecutive duplicate bigrams
        bigrams = [f"{words[i]} {words[i+1]}".lower() for i in range(len(words) - 1)]
        for i in range(1, len(bigrams)):
            if bigrams[i] == bigrams[i - 1]:
                return True

        return False

    @classmethod
    def clean_repetitive_loops(cls, text: str) -> str:
        """Clean obvious immediate consecutive duplicates from output."""
        tokens = text.split()
        if not tokens:
            return text

        deduped = []
        for t in tokens:
            if deduped and t.lower() == deduped[-1].lower():
                continue
            deduped.append(t)
        return " ".join(deduped)

    @classmethod
    def evaluate(
        cls,
        source_text: str,
        translated_text: str,
        src_lang: str,
        tgt_lang: str,
        is_tm_hit: bool = False,
        tm_score: float = 1.0,
        entities_shielded: int = 0,
        entities_restored: int = 0,
    ) -> GuardResult:
        """
        Evaluate translation quality and return calibrated confidence & warnings.
        """
        clean_src = source_text.strip()
        clean_tgt = translated_text.strip()

        # If it's a verified Translation Memory match, confidence is high
        if is_tm_hit:
            conf = max(0.95, round(tm_score, 2))
            return GuardResult(
                confidence=conf,
                is_tm_hit=True,
                is_uncertain=False,
                warning=None,
                clean_translation=clean_tgt,
            )

        confidence = 0.85
        warning: str | None = None
        has_anomaly = False

        src_words = clean_src.split()
        tgt_words = clean_tgt.split()

        # 1. Check repetition
        if cls.detect_repetition(clean_tgt):
            clean_tgt = cls.clean_repetitive_loops(clean_tgt)
            confidence -= 0.30
            has_anomaly = True
            warning = "Repetitive phrasing detected in translation."

        # 2. Check length divergence
        if len(src_words) >= 3 and len(tgt_words) > 0:
            ratio = len(tgt_words) / len(src_words)
            if ratio > 3.2:
                confidence -= 0.35
                has_anomaly = True
                warning = "Translation appears excessively long for the input."
            elif ratio < 0.22 and len(src_words) >= 4:
                confidence -= 0.30
                has_anomaly = True
                warning = "Translation appears truncated."

        # 3. Check entity loss
        if entities_shielded > 0 and entities_restored < entities_shielded:
            confidence -= 0.25
            has_anomaly = True
            warning = "A named entity or title may have been omitted."

        # 4. Check noisy / truncated input
        if len(src_words) == 1 and len(clean_src) < 4:
            confidence -= 0.15
            if not warning:
                warning = "Short utterance; translation may be approximate."

        # Clamp confidence
        final_conf = max(0.20, min(0.95, round(confidence, 2)))
        is_uncertain = final_conf < 0.65 or has_anomaly

        return GuardResult(
            confidence=final_conf,
            is_tm_hit=False,
            is_uncertain=is_uncertain,
            warning=warning,
            clean_translation=clean_tgt,
        )
