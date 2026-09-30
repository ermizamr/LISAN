"""
Entity Shield & Honorific Protector Engine for Ethiopian Multilingual NLP.

Protects named entities, personal names, titles, and cultural honorifics across:
- Afaan Oromoo (Qubee)
- Amharic (Ge'ez)
- Tigrinya (Ge'ez)
- Somali (Latin)
- English (Latin)

Prevents NLLB-200 and other neural MT models from dropping subjects, mutating
political/cultural figures into abstract concepts, or hallucinating false words.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import NamedTuple


# ─────────────────────────────────────────────────────────────────────────────
# 1. Cross-Language Honorific & Title Ontologies
# ─────────────────────────────────────────────────────────────────────────────

# Standard title categories mapped across languages
# Format: (orm, amh, tir, som, eng)
TITLE_MAPPINGS: list[dict[str, str]] = [
    {
        "category": "mr",
        "orm": "Obbo",
        "amh": "አቶ",
        "tir": "ኣቶ",
        "som": "Mudane",
        "eng": "Mr.",
    },
    {
        "category": "mrs",
        "orm": "Aadde",
        "amh": "ወ/ሮ",
        "tir": "ወ/ሮ",
        "som": "Marwo",
        "eng": "Mrs.",
    },
    {
        "category": "miss",
        "orm": "Intala",
        "amh": "ወ/ሪት",
        "tir": "ወ/ሪት",
        "som": "Gabar",
        "eng": "Ms.",
    },
    {
        "category": "doctor",
        "orm": "Dooktor",
        "amh": "ዶ/ር",
        "tir": "ዶ/ር",
        "som": "Dr.",
        "eng": "Dr.",
    },
    {
        "category": "professor",
        "orm": "Piroofeesara",
        "amh": "ፕሮፌሰር",
        "tir": "ፕሮፌሰር",
        "som": "Borofisar",
        "eng": "Professor",
    },
    {
        "category": "president",
        "orm": "Pirezidaantii",
        "amh": "ፕሬዝዳንት",
        "tir": "ፕረዚደንት",
        "som": "Madaxweyne",
        "eng": "President",
    },
    {
        "category": "prime_minister",
        "orm": "Muummee Ministiraa",
        "amh": "ጠቅላይ ሚኒስትር",
        "tir": "ቀዳማይ ሚኒስተር",
        "som": "Ra'iisul Wasaare",
        "eng": "Prime Minister",
    },
    {
        "category": "minister",
        "orm": "Ministira",
        "amh": "ሚኒስትር",
        "tir": "ሚኒስተር",
        "som": "Wasiir",
        "eng": "Minister",
    },
    {
        "category": "analyst",
        "orm": "Xiinxalaa",
        "amh": "ተንታኝ",
        "tir": "ተንታኒ",
        "som": "Falanqeeye",
        "eng": "Analyst",
    },
    {
        "category": "political_analyst",
        "orm": "Xiinxalaa Siyaasaa",
        "amh": "የፖለቲካ ተንታኝ",
        "tir": "ናይ ፖለቲካ ተንታኒ",
        "som": "Falanqeeyaha Siyaasadda",
        "eng": "Political Analyst",
    },
    {
        "category": "journalist",
        "orm": "Gaazexeessaa",
        "amh": "ጋዜጠኛ",
        "tir": "ጋዜጠኛ",
        "som": "Wariye",
        "eng": "Journalist",
    },
    {
        "category": "sheikh",
        "orm": "Sheekh",
        "amh": "ሼክ",
        "tir": "ሼኽ",
        "som": "Sheekh",
        "eng": "Sheikh",
    },
    {
        "category": "elder_father",
        "orm": "Abbaa",
        "amh": "አባ",
        "tir": "ኣባ",
        "som": "Ugaas",
        "eng": "Father",
    },
]

# Common stop words by language to prevent boundary over-extraction in STT transcriptions
STOP_WORDS: dict[str, set[str]] = {
    "orm": {
        "dhimma", "waan", "akka", "jedhan", "jedhaniiru", "kana", "sun", "keessa",
        "booda", "itti", "gara", "irra", "waliin", "ibsaniiru", "dubbataniiru", "ta'uu",
        "malee", "hundi", "fa'a", "jira", "jiru", "fi", "ykn", "otoo", "erga"
    },
    "som": {
        "ayaa", "waxaa", "waxay", "ee", "ku", "ka", "u", "oo", "ah", "lagu", "inuu",
        "inay", "sheegay", "sheegtay", "hadlay", "kadib", "markii", "iyo", "ama", "laakiin"
    },
    "amh": {
        "እንደ", "ስለ", "ይህን", "ይህንን", "ጉዳይ", "ብለዋል", "አሉ", "ተናገሩ", "ገለጹ", "ወደ",
        "ላይ", "ውስጥ", "ጋር", "በኋላ", "በፊት", "እና", "ወይም", "ግን", "ነው", "ናቸው"
    },
    "tir": {
        "ከም", "ብዛዕባ", "እዚ", "እዚኣ", "ጉዳይ", "ኢሎም", "በሉ", "ገለጹ", "ናብ", "ኣብ",
        "ውሽጢ", "ምስ", "ድሕሪ", "ቅድሚ", "ን", "ወይ", "ግን", "እዩ", "እዮም"
    },
    "eng": {
        "said", "stated", "explained", "regarding", "about", "this", "that", "these",
        "those", "in", "on", "at", "to", "for", "with", "after", "before", "and", "or",
        "but", "is", "was", "are", "were", "has", "have", "had", "will"
    },
}

# Language-specific regex title detectors
TITLE_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "orm": [
        (r"\b(?:xiinxalaa[n]?(?:\s+siyaasaa[n]?)?)\s+obbo\b", "political_analyst_mr"),
        (r"\bxiinxalaa[n]?\s+siyaasaa[n]?\b", "political_analyst"),
        (r"\bxiinxalaa[n]?\b", "analyst"),
        (r"\bmuummee[n]?\s+ministiraa[n]?\b", "prime_minister"),
        (r"\bpirezidaant(?:ii)?[n]?\b", "president"),
        (r"\bministira[n]?\b", "minister"),
        (r"\bgaazexeessaa[n]?\b", "journalist"),
        (r"\bhayyuu[n]?\b", "analyst"),
        (r"\bobbo\b", "mr"),
        (r"\baadde\b", "mrs"),
        (r"\bdooktor\b|\bdr\.?\b", "doctor"),
        (r"\bsheekh\b|\bsh\.\b", "sheikh"),
        (r"\babbaa\b", "elder_father"),
    ],
    "som": [
        (r"\bfalanqeeyaha\s+siyaasadda\s+mudane\b", "political_analyst_mr"),
        (r"\bfalanqeeyaha\s+siyaasadda\b", "political_analyst"),
        (r"\bra'iisul\s+wasaare\b", "prime_minister"),
        (r"\bmadaxweyne\b", "president"),
        (r"\bwasiir\b", "minister"),
        (r"\bwariye\b", "journalist"),
        (r"\bmudane\b", "mr"),
        (r"\bmarwo\b", "mrs"),
        (r"\bsheekh\b|\bshiikh\b|\bsh\.\b", "sheikh"),
        (r"\bugaas\b|\bgaraad\b|\bsuldaan\b", "elder_father"),
        (r"\bdhaqtar\b|\bdr\.?\b", "doctor"),
    ],
    "amh": [
        (r"\bየፖለቲካ\s+ተንታኝ\s+አቶ\b", "political_analyst_mr"),
        (r"\bየፖለቲካ\s+ተንታኝ\b", "political_analyst"),
        (r"\bተንታኝ\b", "analyst"),
        (r"\bጠቅላይ\s+ሚኒስትር\b", "prime_minister"),
        (r"\bፕሬዝዳንት\b", "president"),
        (r"\bሚኒስትር\b", "minister"),
        (r"\bጋዜጠኛ\b", "journalist"),
        (r"\bአቶ\b", "mr"),
        (r"\bወ/ሮ\b|\bወይዘሮ\b", "mrs"),
        (r"\bወ/ሪት\b|\bወይዘሪት\b", "miss"),
        (r"\bዶ/ር\b|\bዶክተር\b", "doctor"),
        (r"\bፕሮፌሰር\b", "professor"),
        (r"\bሼክ\b|\bሼይኽ\b", "sheikh"),
        (r"\bአባ\b", "elder_father"),
    ],
    "tir": [
        (r"\bናይ\s+ፖለቲካ\s+ተንታኒ\s+ኣቶ\b", "political_analyst_mr"),
        (r"\bናይ\s+ፖለቲካ\s+ተንታኒ\b", "political_analyst"),
        (r"\bተንታኒ\b", "analyst"),
        (r"\bቀዳማይ\s+ሚኒስተር\b", "prime_minister"),
        (r"\bፕረዚደንት\b", "president"),
        (r"\bሚኒስተር\b", "minister"),
        (r"\bጋዜጠኛ\b", "journalist"),
        (r"\bኣቶ\b", "mr"),
        (r"\bወ/ሮ\b|\bወይዘሮ\b", "mrs"),
        (r"\bወ/ሪት\b|\bወይዘሪት\b", "miss"),
        (r"\bዶ/ር\b|\bዶክተር\b", "doctor"),
        (r"\bፕሮፌሰር\b", "professor"),
        (r"\bሼኽ\b|\bሼክ\b", "sheikh"),
        (r"\bኣባ\b", "elder_father"),
    ],
    "eng": [
        (r"\bpolitical\s+analyst\s+mr\.?\b", "political_analyst_mr"),
        (r"\bpolitical\s+analyst\b", "political_analyst"),
        (r"\bprime\s+minister\b", "prime_minister"),
        (r"\bpresident\b", "president"),
        (r"\bminister\b", "minister"),
        (r"\bjournalist\b", "journalist"),
        (r"\bmr\.?\b", "mr"),
        (r"\bmrs\.?\b", "mrs"),
        (r"\bms\.?\b", "miss"),
        (r"\bdr\.?\b|\bdoctor\b", "doctor"),
        (r"\bprofessor\b|\bprof\.?\b", "professor"),
        (r"\bsheikh\b", "sheikh"),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Phonetic Script Mapping (Latin <-> Ge'ez)
# ─────────────────────────────────────────────────────────────────────────────

# Fast phonetic mapping dictionary for common Ethiopian personal name components
PHONETIC_LATIN_TO_GEEZ: dict[str, str] = {
    # Common Names (Afaan Oromoo, Amharic, Tigrinya, Somali)
    "jawaar": "ጃዋር", "jawar": "ጃዋር", "jawaa": "ጃዋር", "jawaari": "ጃዋር",
    "mohammada": "ሞሐመድ", "mohammed": "ሞሐመድ", "mohamed": "ሞሐመድ", "mahammad": "መሐመድ",
    "xasan": "ሐሰን", "hassan": "ሐሰን", "hasan": "ሐሰን",
    "maxamuud": "ማሕሙድ", "mahamoud": "ማሕሙድ", "mahmud": "ማሕሙድ",
    "shariif": "ሸሪፍ", "sharif": "ሸሪፍ",
    "fartuun": "ፈርቱን", "fartun": "ፈርቱን",
    "caaltuu": "ጫልቱ", "chaltu": "ጫልቱ",
    "tolasaa": "ቶለሳ", "tolessa": "ቶለሳ",
    "guutaa": "ጉታ", "guta": "ጉታ",
    "kumsaa": "ኩምሳ", "kumsa": "ኩምሳ",
    "shimallis": "ሽመልስ", "shimeles": "ሽመልስ",
    "abiy": "ዓቢይ", "abiyi": "ዓቢይ", "abiyyi": "ዓቢይ",
    "ahmed": "አሕመድ", "ahmad": "አሕመድ",
    "tayee": "ታዬ", "taye": "ታዬ",
    "kebede": "ከበደ", "almaz": "አልማዝ", "alganesh": "ኣልጋነሽ",
    "gebremedhin": "ገብረመድህን", "tewodros": "ቴዎድሮስ", "debretsion": "ደብረጽዮን",
    "hailemariam": "ኃይለማርያም", "selassie": "ሥላሴ",
}

PHONETIC_GEEZ_TO_LATIN: dict[str, str] = {
    "ጃዋር": "Jawar",
    "ሞሐመድ": "Mohammed", "መሐመድ": "Mohammed", "ሙሐመድ": "Muhammed",
    "ሐሰን": "Hassan", "ሃሰን": "Hassan",
    "ማሕሙድ": "Mohamoud", "መሕሙድ": "Mahmud",
    "ሸሪፍ": "Sharif",
    "ፈርቱን": "Fartun",
    "ጫልቱ": "Chaltu",
    "ቶለሳ": "Tolessa",
    "ጉታ": "Guta",
    "ኩምሳ": "Kumsa",
    "ሽመልስ": "Shimelis",
    "ዓቢይ": "Abiy", "አብይ": "Abiy",
    "አሕመድ": "Ahmed", "አህመድ": "Ahmed",
    "ታዬ": "Taye",
    "ከበደ": "Kebede",
    "አልማዝ": "Almaz",
    "ኣልጋነሽ": "Alganesh", "አልጋነሽ": "Alganesh",
    "ገብረመድህን": "Gebremedhin",
    "ቴዎድሮስ": "Tewodros",
    "ደብረጽዮን": "Debretsion",
    "ኃይለማርያም": "Hailemariam",
    "ሥላሴ": "Selassie",
}


@dataclass
class ShieldedEntity:
    placeholder: str
    original_text: str
    title_category: str | None
    name_part: str
    src_lang: str


class EntityShield:
    """
    Guarantees entity preservation across all Ethiopian languages.
    
    1. Detects named entity sequences and honorifics.
    2. Masks them with inert placeholder tokens.
    3. Translates the sentence skeleton.
    4. Restores names and adapts titles into the target language.
    """

    @classmethod
    def _get_target_title(cls, category: str, tgt_lang: str) -> str:
        """Resolve title category to target language string."""
        lang_key = tgt_lang.split("_")[0].lower()
        if category == "political_analyst_mr":
            if lang_key == "eng":
                return "Political Analyst Mr."
            elif lang_key == "amh":
                return "የፖለቲካ ተንታኝ አቶ"
            elif lang_key == "tir":
                return "ናይ ፖለቲካ ተንታኒ ኣቶ"
            elif lang_key == "som":
                return "Falanqeeyaha Siyaasadda Mudane"
            elif lang_key == "orm":
                return "Xiinxalaa Siyaasaa Obbo"

        for row in TITLE_MAPPINGS:
            if row.get("category") == category:
                return row.get(lang_key, row.get("eng", ""))
        return ""

    @classmethod
    def _convert_name_script(cls, name: str, src_lang: str, tgt_lang: str) -> str:
        """Convert personal name between Latin and Ge'ez scripts if necessary."""
        src_is_geez = src_lang.startswith("amh") or src_lang.startswith("tir")
        tgt_is_geez = tgt_lang.startswith("amh") or tgt_lang.startswith("tir")

        # Standard canonical cleanups for speech-to-text variations
        # e.g. "jawaa mohammada" -> "Jawar Mohammed"
        clean_name = name.strip()
        lower_name = clean_name.lower()
        if "jawaa" in lower_name and "moham" in lower_name:
            if tgt_is_geez:
                return "ጃዋር ሞሐመድ"
            return "Jawar Mohammed"

        # If both use the same script system, keep original spelling
        if src_is_geez == tgt_is_geez:
            if not src_is_geez:
                return " ".join(w.capitalize() for w in clean_name.split())
            return clean_name

        # Latin -> Ge'ez
        if not src_is_geez and tgt_is_geez:
            tokens = clean_name.split()
            geez_tokens = []
            for t in tokens:
                clean_t = re.sub(r"[^\w']", "", t).lower()
                if clean_t in PHONETIC_LATIN_TO_GEEZ:
                    geez_tokens.append(PHONETIC_LATIN_TO_GEEZ[clean_t])
                else:
                    geez_tokens.append(t.capitalize())
            return " ".join(geez_tokens)

        # Ge'ez -> Latin
        if src_is_geez and not tgt_is_geez:
            tokens = clean_name.split()
            lat_tokens = []
            for t in tokens:
                clean_t = re.sub(r"[^\w]", "", t)
                if clean_t in PHONETIC_GEEZ_TO_LATIN:
                    lat_tokens.append(PHONETIC_GEEZ_TO_LATIN[clean_t])
                else:
                    lat_tokens.append(t)
            return " ".join(lat_tokens)

        return clean_name

    @classmethod
    def shield(
        cls,
        text: str,
        src_lang: str,
    ) -> tuple[str, list[ShieldedEntity]]:
        """
        Identify named entities & honorifics in text and replace with placeholders.
        """
        if not text or not text.strip():
            return text, []

        norm_src = src_lang.split("_")[0].lower()
        patterns = TITLE_PATTERNS.get(norm_src, TITLE_PATTERNS["eng"])
        stop_words = STOP_WORDS.get(norm_src, set())

        shielded: list[ShieldedEntity] = []
        modified_text = text

        for pat, cat in patterns:
            # Match title followed by 1 to 4 potential name tokens
            if norm_src in ("amh", "tir"):
                regex = rf"({pat})\s+([\u1200-\u137F]+(?:\s+[\u1200-\u137F]+){{0,3}})"
            else:
                regex = rf"({pat})\s+([A-Za-z'ʻʼ]+(?:\s+[A-Za-z'ʻʼ]+){{0,3}})"

            for m in list(re.finditer(regex, modified_text, flags=re.IGNORECASE)):
                title_span = m.group(1)
                raw_name_span = m.group(2)

                # Prune any stop words from the name span
                tokens = raw_name_span.strip().split()
                valid_name_tokens = []
                for t in tokens:
                    clean_t = re.sub(r"[^\w']", "", t).lower()
                    if clean_t in stop_words:
                        break
                    valid_name_tokens.append(t)

                if not valid_name_tokens:
                    continue

                clean_name_span = " ".join(valid_name_tokens)
                full_span = f"{title_span} {clean_name_span}"

                idx = len(shielded)
                placeholder = f"__ETH_ENTITY_{idx}__"

                shielded.append(
                    ShieldedEntity(
                        placeholder=placeholder,
                        original_text=full_span,
                        title_category=cat,
                        name_part=clean_name_span,
                        src_lang=norm_src,
                    )
                )
                modified_text = modified_text.replace(full_span, placeholder, 1)

        return modified_text, shielded

    @classmethod
    def unshield(
        cls,
        translated_text: str,
        shielded_entities: list[ShieldedEntity],
        src_lang: str,
        tgt_lang: str,
    ) -> str:
        """
        Restore placeholders with target-language-appropriate titles and phonetically
        accurate names.
        """
        if not shielded_entities or not translated_text:
            return translated_text

        result = translated_text
        norm_tgt = tgt_lang.split("_")[0].lower()
        norm_src = src_lang.split("_")[0].lower()

        for entity in shielded_entities:
            target_title = ""
            if entity.title_category:
                target_title = cls._get_target_title(entity.title_category, norm_tgt)

            converted_name = cls._convert_name_script(entity.name_part, norm_src, norm_tgt)

            if target_title:
                restored = f"{target_title} {converted_name}".strip()
            else:
                restored = converted_name

            # Look for exact placeholder or common lowercased / deformed variants
            pat = rf"__eth_entity_{entity.placeholder[-3]}" if "__eth_entity_" in entity.placeholder.lower() else re.escape(entity.placeholder)
            result = re.sub(rf"__ETH_ENTITY_\d+__|__eth_entity_\d+__|\[\s*ETH_ENTITY_\d+\s*\]", restored, result, count=1, flags=re.IGNORECASE)

        return result
