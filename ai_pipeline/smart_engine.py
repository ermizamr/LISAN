"""Offline Smart Engine for Ethiopian Translator ("Lisan Intelligence").

Provides context-aware multi-turn reasoning, intent classification,
cultural idiom de-literalization, formality register control, and
intelligent follow-up suggestion chips — 100% on-device and memory-safe.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntentType(str, Enum):
    GREETING = "greeting_courtesy"
    BARGAINING = "commerce_bargaining"
    DIRECTIONS = "navigation_directions"
    DINING = "dining_hospitality"
    MEDICAL = "emergency_medical"
    GENERAL = "general_conversation"


# ──────────────────────────────────────────────────────────────────
# 1. Cultural Idioms & Figurative Expressions De-literalizer
# ──────────────────────────────────────────────────────────────────
AMHARIC_IDIOMS: list[tuple[str, str]] = [
    # Encouragement, sympathy & comfort
    (r"\bአይዞህ\b", "Take heart / Stay strong"),
    (r"\bአይዞሽ\b", "Take heart / Stay strong"),
    (r"\bአይዟችሁ\b", "Take heart / Stay strong everyone"),
    (r"\bአትጨነቅ\b", "Don't worry"),
    (r"\bአትጨነቂ\b", "Don't worry"),
    (r"\bአትጨነቁ\b", "Don't worry everyone"),
    # Congratulations & blessings
    (r"\bእንኳን ደስ አለህ\b", "Congratulations!"),
    (r"\bእንኳን ደስ አለሽ\b", "Congratulations!"),
    (r"\bእንኳን ደስ አላችሁ\b", "Congratulations everyone!"),
    (r"\bእንኳን አደረሰህ\b", "Happy holiday / Season's greetings!"),
    (r"\bእንኳን አደረሰሽ\b", "Happy holiday / Season's greetings!"),
    (r"\bእንኳን አደረሳችሁ\b", "Happy holiday / Season's greetings to all!"),
    (r"\bእግዜር ይስጥልኝ\b", "Thank you very much / May God reward you"),
    (r"\bእግዚአብሔር ይስጥልኝ\b", "Thank you very much / May God reward you"),
    (r"\bመልካም ቀን\b", "Have a wonderful day"),
    (r"\bመልካም እድል\b", "Good luck"),
    (r"\bእሰይ\b", "Wonderful / Hooray"),
    # Colloquial idioms
    (r"\bሆዴ ባባ\b", "I was deeply moved with emotion"),
    (r"\bበቁም ነገር\b", "In all seriousness"),
    (r"\bእግር አውጣ ብዬ\b", "I ran as fast as I could"),
    (r"\bስራ ፈታሁ\b", "I am out of work / I am free"),
    (r"\bእንደምንም ብዬ\b", "Somehow / by any means necessary"),
    (r"\bምን አገባኝ\b", "None of my business"),
    (r"\bበቃ\b", "That is all / Enough"),
    (r"\bምንም አይደል\b", "Don't mention it / No problem"),
    (r"\bቸር ያሰማን\b", "May we hear good news"),
]

OROMO_IDIOMS: list[tuple[str, str, str]] = [
    (r"\bharka fuune\b", "Greetings / Welcome", "ሰላምታ አቅርበናል።"),
    (r"\bbaga nagaan dhufte\b", "Welcome! Glad you arrived safely", "እንኳን ደህና መጣህ።"),
    (r"\bbaga nagaan dhuftan\b", "Welcome everyone! Glad you arrived safely", "እንኳን ደህና መጣችሁ።"),
    (r"\brakkoo hin qabu\b", "No problem / Don't worry at all", "ምንም ችግር የለም።"),
    (r"\bfayyaa qabaadhu\b", "Stay healthy and take care", "ጤና ይኑርህ፣ ደህና ሁን።"),
    (r"\bnagaan oolaa\b", "Have a peaceful and wonderful day", "መልካም ቀን ይሁንላችሁ።"),
    (r"\babdii hin kutatin\b", "Don't lose hope / Take courage", "ተስፋ አትቁረጥ / አይዞህ።"),
    (r"\bwanti hundi gaarii dha\b", "Everything is going well", "ሁሉም ነገር ጥሩ ነው።"),
]

TIGRINYA_IDIOMS: list[tuple[str, str, str]] = [
    # Broadcast & Media Introductions
    (r"\bጥዕና\s+ይሃበለይ\s+ከመይ\s+(?:ዲኹም|ኣለኹም)\s+(?:ዝኸበርኩም|ክቡራት)\s+(?:ተመልከትትና|ተዓዘብትና)\b",
     "Hello, how are you honored viewers.",
     "ጤና ይስጥልኝ፣ ክቡራት ተመልካቾቻችን እንደምን ናችሁ።"),
    (r"\bጥዕና\s+ይሃበለይ\s+ከመይ\s+(?:ዲኹም|ኣለኹም)\s+(?:ዝኸበርኩም|ክቡራት)\s+ሰማዕትና\b",
     "Hello, how are you honored listeners.",
     "ጤና ይስጥልኝ፣ ክቡራት አድማጮቻችን እንደምን ናችሁ።"),
    (r"\bጥዕና\s+ይሃበለይ\s+ከመይ\s+(?:ዲኹም|ኣለኹም)\b",
     "Hello, how are you all?",
     "ጤና ይስጥልኝ፣ እንደምን ናችሁ?"),
    (r"\bጥዕና\s+ይሃበለይ\b",
     "Hello / Greetings",
     "ጤና ይስጥልኝ።"),
    (r"\b(?:ዝኸበርኩም|ክቡራት)\s+(?:ተመልከትትና|ተዓዘብትና)\b",
     "Honored viewers",
     "ክቡራት ተመልካቾቻችን"),
    (r"\b(?:ዝኸበርኩም|ክቡራት)\s+ሰማዕትና\b",
     "Honored listeners",
     "ክቡራት አድማጮቻችን"),
    # Courtesies & Comfort
    (r"\bእንቋዕ ብደሓን መጻእካ\b", "Welcome! Glad you arrived safely", "እንኳን ደህና መጣህ።"),
    (r"\bእንቋዕ ብደሓን መጻእኪ\b", "Welcome! Glad you arrived safely", "እንኳን ደህና መጣሽ።"),
    (r"\bእንቋዕ ብደሓን መጻእኩም\b", "Welcome everyone! Glad you arrived safely", "እንኳን ደህና መጣችሁ።"),
    (r"\bኣጆኻ\b", "Stay strong / Take courage", "አይዞህ / በርታ።"),
    (r"\bኣጆኺ\b", "Stay strong / Take courage", "አይዞሽ / በርቺ።"),
    (r"\bኣጆኹም\b", "Stay strong everyone", "አይዟችሁ / በርቱ።"),
    (r"\bእግዚኣብሔር ይሃበለይ\b", "May God reward you / Thank you so much", "እግዚአብሔር ይስጥልኝ።"),
    (r"\bጸገም የለን\b", "No problem / Don't mention it", "ምንም ችግር የለም።"),
    (r"\bቡሩኽ መዓልቲ\b", "Have a blessed day", "የተባረከ ቀን ይሁንልህ።"),
    (r"\bኣይትጨነቕ\b", "Don't worry", "አትጨነቅ።"),
]

SOMALI_IDIOMS: list[tuple[str, str, str]] = [
    (r"\bsoo dhawoow\b", "Welcome!", "እንኳን ደህና መጣህ።"),
    (r"\bsoo dhowow\b", "Welcome!", "እንኳን ደህና መጣህ።"),
    (r"\bdhib ma leh\b", "No problem / Don't worry", "ምንም ችግር የለም።"),
    (r"\bha walwalin\b", "Don't worry", "አትጨነቅ።"),
    (r"\bnasiib wacan\b", "Good luck!", "መልካም እድል!"),
    (r"\bmaalin wanaagsan\b", "Have a wonderful day", "መልካም ቀን።"),
]


class CulturalIdiomEngine:
    """Matches and replaces cultural figures of speech with true semantic equivalents."""

    @classmethod
    def match_cultural_idiom(cls, text: str, src_lang: str, tgt_lang: str = "eng") -> str | None:
        if not text:
            return None
        cleaned = text.strip()
        stripped = re.sub(r"[.!?፣።፧\s]+$", "", cleaned)
        is_target_amh = tgt_lang in ("amh", "amh_Ethi")

        idiom_tables = {
            ("amh", "amh_Ethi"): AMHARIC_IDIOMS,
            ("orm", "gaz_Latn"): OROMO_IDIOMS,
            ("tir", "tir_Ethi"): TIGRINYA_IDIOMS,
            ("som", "som_Latn"): SOMALI_IDIOMS,
        }

        # Defer compound multi-clause sentences to the pipeline's clause-level translator
        multi_clauses = [c.strip() for c in re.split(r'(?<=[.?!።፧!])\s+', cleaned) if c.strip()]
        if len(multi_clauses) > 1:
            return None

        text_words = len(stripped.split())
        for keys, table in idiom_tables.items():
            if src_lang in keys:
                for entry in table:
                    pattern = entry[0]
                    clean_pat = pattern.removeprefix("(?i)")
                    pat_words = len(re.sub(r"[^\w\s]", "", clean_pat).split())
                    # Only match if the utterance is primarily the idiom
                    if text_words <= max(pat_words + 3, 5):
                        if (re.search(clean_pat, cleaned, flags=re.IGNORECASE) or
                                re.search(clean_pat, stripped, flags=re.IGNORECASE)):
                            if is_target_amh and len(entry) >= 3:
                                return entry[2]
                            return entry[1]
                break

        return None


# ──────────────────────────────────────────────────────────────────
# 2. Intent Classifier
# ──────────────────────────────────────────────────────────────────
class IntentClassifier:
    """Fast rule-based domain and dialogue intent classifier."""

    INTENT_KEYWORDS: dict[IntentType, list[str]] = {
        IntentType.GREETING: [
            "hello", "hi", "how are you", "good morning", "good evening", "goodbye", "bye", "thanks", "thank you",
            "ሰላም", "እንዴት", "እንደምን", "ደህና", "ቻው", "አመሰግናለሁ", "አመሰግናለው",
            "akkam", "nagaa", "fayyaa", "fayyumaa", "fayyummaa", "jirta", "jirtu", "bulte", "oolte", "galatoomi", "galatoomaa",
            "ከመይ", "ደሓን", "የቐንየለይ", "ብሩህ", "ጥዕና", "ጥዕና ይሃበለይ",
            "iska warran", "sidee", "subax", "nabad", "mahadsanid",
        ],
        IntentType.BARGAINING: [
            "how much", "cost", "price", "expensive", "discount", "cheap", "birr", "pay", "money", "dollar",
            "ስንት", "ዋጋ", "ብር", "ውድ", "ቅናሽ", "ክፈል", "ገንዘብ",
            "meeqa", "gatii", "qaalii", "hir'isi",
            "ክንዲ ምንታይ", "ዋጋ", "ቅርሺ", "ክቡር", "ኣጉድለለይ",
            "immisa", "qiimo", "qaali", "dhim",
        ],
        IntentType.DIRECTIONS: [
            "where", "how to get", "far", "near", "left", "right", "straight", "taxi", "bus", "station", "hotel", "airport",
            "የት", "ሩቅ", "ቅርብ", "ቀኝ", "ግራ", "ቀጥታ", "ታክሲ", "አውቶቡስ", "ሆቴል", "ኤርፖርት",
            "eessa", "fagoo", "dhihoo", "mirga", "bitaa", "taaksii", "hoteela",
            "ኣበይ", "ርሑቕ", "ቐረባ", "የማን", "ጸጋም", "ታክሲ", "ሆቴል",
            "xaggee", "dhow", "fog", "midig", "bidix", "tagsi", "huteel",
        ],
        IntentType.DINING: [
            "food", "water", "drink", "eat", "coffee", "tea", "menu", "restaurant", "injera", "shiro", "doro", "bill",
            "ምግብ", "ውሃ", "መጠጥ", "ቡና", "ሻይ", "ሬስቶራንት", "እንጀራ", "ሽሮ", "ዶሮ", "ሒሳብ",
            "nyaata", "bishaan", "dhugii", "buna", "shaayee", "injiiraa",
            "ምግቢ", "ማይ", "ቡን", "ሻሂ", "እንጀራ", "ሒሳብ",
            "cunto", "biyo", "cab", "bun", "shaah", "biil",
        ],
        IntentType.MEDICAL: [
            "hospital", "doctor", "medicine", "pharmacy", "sick", "pain", "hurt", "emergency", "ambulance", "help", "police",
            "ሆስፒታል", "ሐኪም", "መድሃኒት", "ፋርማሲ", "ህመም", "ታምሜያለሁ", "እርዳታ", "ፖሊስ", "አምቡላንስ", "እርዳኝ",
            "hospitaala", "doktora", "qoricha", "dhukkuba", "gargaarsa",
            "ሆስፒታል", "ሓኪም", "መድሃኒት", "ሕሙም", "ሓግዘኒ", "ፖሊስ",
            "cosbitaal", "dhakhtar", "dawo", "xanuun", "caawin", "booliis",
        ],
    }

    @classmethod
    def classify(cls, text: str) -> IntentType:
        if not text:
            return IntentType.GENERAL

        normalized = text.lower()
        scores: dict[IntentType, int] = {intent: 0 for intent in IntentType}

        for intent, keywords in cls.INTENT_KEYWORDS.items():
            for kw in keywords:
                # Word-boundary check matching both Latin words and Ge'ez words
                pattern = r"(?:\b|^|\s)" + re.escape(kw.lower()) + r"(?:\b|$|\s|[!?,.:;፣።፧])"
                if re.search(pattern, normalized):
                    scores[intent] += 1

        best_intent = max(scores, key=scores.get)  # type: ignore
        return best_intent if scores[best_intent] > 0 else IntentType.GENERAL


# ──────────────────────────────────────────────────────────────────
# 3. Formality & Register Controller
# ──────────────────────────────────────────────────────────────────
class FormalityController:
    """Adapts translation phrasing between honorific/polite and familiar/casual registers."""

    @classmethod
    def apply_formality(cls, text: str, tgt_lang: str, formality: str) -> str:
        if not text or formality not in ("polite", "formal"):
            return text

        result = text
        # If targeting Amharic: elevate familiar 'ነህ/ነሽ' to honorific 'እርስዎ / ኖት'
        if tgt_lang in ("amh", "amh_Ethi"):
            result = re.sub(r"\bእንዴት ነህ\b", "እንዴት ኖት", result)
            result = re.sub(r"\bእንዴት ነሽ\b", "እንዴት ኖት", result)
            result = re.sub(r"\bደህና ነህ\b", "ደህና ኖት", result)
            result = re.sub(r"\bደህና ነሽ\b", "ደህና ኖት", result)
            result = re.sub(r"\bእባክህ\b", "እባክዎ", result)
            result = re.sub(r"\bእባክሽ\b", "እባክዎ", result)
            result = re.sub(r"\bአመሰግናለሁ\b", "እጅግ አድርጌ አመሰግናለሁ", result)

        # If targeting Tigrinya: elevate familiar to plural/honorific 'ኣለኹም'
        elif tgt_lang in ("tir", "tir_Ethi"):
            result = re.sub(r"\bከመይ ኣለኻ\b", "ከመይ ኣለኹም", result)
            result = re.sub(r"\bከመይ ኣለኺ\b", "ከመይ ኣለኹም", result)
            result = re.sub(r"\bደሓን ዲኻ\b", "ደሓን ዲኹም", result)
            result = re.sub(r"\bደሓን ዲኺ\b", "ደሓን ዲኹም", result)
            result = re.sub(r"\bበጃኻ\b", "በጃኹም", result)
            result = re.sub(r"\bበጃኺ\b", "በጃኹም", result)

        return result


# ──────────────────────────────────────────────────────────────────
# 4. Multi-Turn Context Manager
# ──────────────────────────────────────────────────────────────────
@dataclass
class ConversationTurn:
    turn_id: int
    src_lang: str
    tgt_lang: str
    source_text: str
    translated_text: str
    intent: IntentType
    timestamp: float = field(default_factory=time.time)


class SmartContextManager:
    """Tracks dialogue history and resolves contextual ellipsis."""

    _sessions: dict[str, list[ConversationTurn]] = {}

    @classmethod
    def get_history(cls, session_id: str) -> list[ConversationTurn]:
        return cls._sessions.get(session_id, [])

    @classmethod
    def add_turn(
        cls,
        session_id: str,
        src_lang: str,
        tgt_lang: str,
        source_text: str,
        translated_text: str,
        intent: IntentType,
    ) -> None:
        if session_id not in cls._sessions:
            cls._sessions[session_id] = []
        turns = cls._sessions[session_id]
        turns.append(
            ConversationTurn(
                turn_id=len(turns) + 1,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                source_text=source_text,
                translated_text=translated_text,
                intent=intent,
            )
        )
        # Keep maximum 10 recent turns to preserve memory
        if len(turns) > 10:
            cls._sessions[session_id] = turns[-10:]

    @classmethod
    def resolve_contextual_ellipsis(cls, text: str, src_lang: str, session_id: str | None) -> str:
        """Resolve short queries (e.g. 'Where is it?', 'How much?') using recent entities."""
        if not session_id or session_id not in cls._sessions:
            return text

        history = cls._sessions[session_id]
        if not history:
            return text

        last_turn = history[-1]
        resolved = text.strip()

        # Entity extraction from previous turn (e.g., taxi, hospital, hotel)
        prev_text = (last_turn.source_text + " " + last_turn.translated_text).lower()

        entity = None
        if "hospital" in prev_text or "ሆስፒታል" in prev_text or "hospitaala" in prev_text:
            entity = ("hospital", "ሆስፒታል", "hospitaalichi", "ሆስፒታል")
        elif "taxi" in prev_text or "ታክሲ" in prev_text or "taaksii" in prev_text:
            entity = ("taxi", "ታክሲ", "taaksii", "ታክሲ")
        elif "hotel" in prev_text or "ሆቴል" in prev_text:
            entity = ("hotel", "ሆቴል", "hoteela", "ሆቴል")
        elif "water" in prev_text or "ውሃ" in prev_text or "bishaan" in prev_text:
            entity = ("water", "ውሃ", "bishaan", "ማይ")

        if entity:
            # If user asks "Where is it?" -> "Where is the [entity]?"
            if resolved.lower() in ("where is it", "where is it?", "where is that", "where?"):
                resolved = f"Where is the {entity[0]}?"
            elif resolved in ("የት ነው", "የት ነው?", "የት"):
                resolved = f"{entity[1]} የት ነው?"
            elif resolved.lower() in ("eessa jira", "eessa jira?", "eessa?"):
                resolved = f"{entity[2]} eessa jira?"
            elif resolved in ("ኣበይ ኣሎ", "ኣበይ ኣሎ?", "ኣበይ"):
                resolved = f"{entity[3]} ኣበይ ኣሎ?"

            # If user asks "How much?" -> "How much is the [entity]?"
            elif resolved.lower() in ("how much", "how much?", "how much is it", "how much is it?"):
                resolved = f"How much is the {entity[0]}?"
            elif resolved in ("ስንት ነው", "ስንት ነው?", "ስንት"):
                resolved = f"የ{entity[1]} ዋጋ ስንት ነው?"

        return resolved


# ──────────────────────────────────────────────────────────────────
# 5. Smart Quick-Reply Suggestions Engine
# ──────────────────────────────────────────────────────────────────
class SmartSuggestionsEngine:
    """Generates relevant contextual reply chips for the other speaker."""

    SUGGESTIONS_MAP: dict[IntentType, dict[str, list[dict[str, str]]]] = {
        IntentType.GREETING: {
            "amh": [
                {"text": "ደህና ነኝ አመሰግናለሁ", "translation": "I am fine, thank you."},
                {"text": "አንተስ እንዴት ነህ?", "translation": "And how are you?"},
                {"text": "ስላገኘሁህ ደስ ብሎኛል", "translation": "Nice to meet you."},
            ],
            "eng": [
                {"text": "I'm doing well, thank you!", "translation": "ደህና ነኝ አመሰግናለሁ!"},
                {"text": "How are you doing today?", "translation": "ዛሬ እንዴት ነህ?"},
                {"text": "Nice to meet you!", "translation": "ስላገኘሁህ ደስ ብሎኛል!"},
            ],
            "orm": [
                {"text": "Fayyaa dha, galatoomi.", "translation": "I am fine, thank you."},
                {"text": "Akkam jirta ati?", "translation": "And how are you?"},
                {"text": "Si arguun koo gammachuu dha.", "translation": "Nice to meet you."},
            ],
            "tir": [
                {"text": "ደሓን እየ የቐንየለይ።", "translation": "I am fine, thank you."},
                {"text": "ንስኻኸ ከመይ ኣለኻ?", "translation": "And how are you?"},
                {"text": "ምስራኸብና ደስ ኢሉኒ።", "translation": "Nice to meet you."},
            ],
            "som": [
                {"text": "Waan fiicanahay, mahadsanid.", "translation": "I am fine, thank you."},
                {"text": "Adiguna sidee tahay?", "translation": "And how are you?"},
                {"text": "Waan ku faraxsanahay la kulankaaga.", "translation": "Nice to meet you."},
            ],
        },
        IntentType.BARGAINING: {
            "amh": [
                {"text": "ቅናሽ አድርግልኝ", "translation": "Can you give me a discount?"},
                {"text": "በጣም ውድ ነው", "translation": "It is too expensive."},
                {"text": "እሺ እወስደዋለሁ", "translation": "Okay, I will take it."},
            ],
            "eng": [
                {"text": "Can you give me a discount?", "translation": "ቅናሽ ልታደርግልኝ ትችላለህ?"},
                {"text": "It is a bit too expensive.", "translation": "ትንሽ ውድ ነው።"},
                {"text": "Okay, I will buy it.", "translation": "እሺ እገዛዋለሁ።"},
            ],
            "orm": [
                {"text": "Gatii naaf hir'isi.", "translation": "Can you give me a discount?"},
                {"text": "Baay'ee qaalii dha.", "translation": "It is too expensive."},
                {"text": "Tole nan fudhadha.", "translation": "Okay, I will take it."},
            ],
            "tir": [
                {"text": "ዋጋ ኣጉድለለይ።", "translation": "Can you give me a discount?"},
                {"text": "ብጣዕሚ ክቡር እዩ።", "translation": "It is too expensive."},
                {"text": "ሕራይ ክወስዶ እየ።", "translation": "Okay, I will take it."},
            ],
            "som": [
                {"text": "Qiimaha iiga dhim.", "translation": "Can you give me a discount?"},
                {"text": "Aad bay qaali u tahay.", "translation": "It is too expensive."},
                {"text": "Haye waan qaadanayaa.", "translation": "Okay, I will take it."},
            ],
        },
        IntentType.DIRECTIONS: {
            "amh": [
                {"text": "ሩቅ ነው?", "translation": "Is it far from here?"},
                {"text": "በእግር መሄድ እችላለሁ?", "translation": "Can I walk there?"},
                {"text": "ታክሲ የት ይገኛል?", "translation": "Where can I find a taxi?"},
            ],
            "eng": [
                {"text": "Is it within walking distance?", "translation": "በእግር መድረስ ይቻላል?"},
                {"text": "How many minutes will it take?", "translation": "ስንት ደቂቃ ይወስዳል?"},
                {"text": "Could you show me on the map?", "translation": "በካርታው ላይ ልታሳየኝ ትችላለህ?"},
            ],
            "orm": [
                {"text": "Fagoo dhaa asirraa?", "translation": "Is it far from here?"},
                {"text": "Miilaan deemuu nan danda'aa?", "translation": "Can I walk there?"},
                {"text": "Taaksii eessatti argadha?", "translation": "Where can I find a taxi?"},
            ],
            "tir": [
                {"text": "ካብዚ ርሑቕ ድዩ?", "translation": "Is it far from here?"},
                {"text": "ብእግሪ ክኸይድ ይኽእልዶ?", "translation": "Can I walk there?"},
                {"text": "ታክሲ ኣበይ ክረክብ ይኽእል?", "translation": "Where can I find a taxi?"},
            ],
            "som": [
                {"text": "Miyaanay fogayn halkaan?", "translation": "Is it far from here?"},
                {"text": "Lug ma ku tagi karaa?", "translation": "Can I walk there?"},
                {"text": "Xaggee ka heli karaa tagsi?", "translation": "Where can I find a taxi?"},
            ],
        },
        IntentType.DINING: {
            "amh": [
                {"text": "ውሃ እፈልጋለሁ", "translation": "I would like water."},
                {"text": "ምግብ ምን አለ?", "translation": "What food is available?"},
                {"text": "ሒሳብ ስንት ነው?", "translation": "How much is the bill?"},
            ],
            "eng": [
                {"text": "Could I get a glass of water?", "translation": "አንድ ብርጭቆ ውሃ ማግኘት እችላለሁ?"},
                {"text": "What do you recommend to eat?", "translation": "ምን ምግብ ትመክረኛለህ?"},
                {"text": "May I have the bill, please?", "translation": "እባክህ ሒሳቡን ልታመጣልኝ?"},
            ],
            "orm": [
                {"text": "Bishaan barbaada.", "translation": "I would like water."},
                {"text": "Nyaata maalitu jira?", "translation": "What food is available?"},
                {"text": "Gatiin meeqa?", "translation": "How much is the bill?"},
            ],
            "tir": [
                {"text": "ማይ እደሊ ኣለኹ።", "translation": "I would like water."},
                {"text": "ምን ኣይነት ምግቢ ኣሎ?", "translation": "What food is available?"},
                {"text": "ሒሳብ ክንዲ ምንታይ እዩ?", "translation": "How much is the bill?"},
            ],
            "som": [
                {"text": "Biyo baan rabaa.", "translation": "I would like water."},
                {"text": "Cunto noocee ah ayaa jirta?", "translation": "What food is available?"},
                {"text": "Biilka iikeen fadlan.", "translation": "Bring the bill, please."},
            ],
        },
        IntentType.MEDICAL: {
            "amh": [
                {"text": "እባክህ እርዳኝ", "translation": "Please help me."},
                {"text": "ሆስፒታል መሄድ አለብኝ", "translation": "I must get to a hospital."},
                {"text": "ህመም ይሰማኛል", "translation": "I feel unwell / sick."},
            ],
            "eng": [
                {"text": "Please call an ambulance / doctor.", "translation": "እባክህ አምቡላንስ / ሐኪም ጥሩልኝ።"},
                {"text": "Where is the nearest pharmacy?", "translation": "በአቅራቢያው ያለ ፋርማሲ የት ነው?"},
                {"text": "I need immediate medical help.", "translation": "አስቸኳይ የህክምና እርዳታ እፈልጋለሁ።"},
            ],
            "orm": [
                {"text": "Maaloo na gargaaraa.", "translation": "Please help me."},
                {"text": "Hospitaala deemuun qaba.", "translation": "I must go to a hospital."},
                {"text": "Dhukkubni natti dhaga'ama.", "translation": "I feel sick / unwell."},
            ],
            "tir": [
                {"text": "በጃኻ ሓግዘኒ።", "translation": "Please help me."},
                {"text": "ናብ ሆስፒታል ክኸይድ ኣለኒ።", "translation": "I must go to a hospital."},
                {"text": "ሕማም ይስመዓኒ ኣሎ።", "translation": "I feel unwell."},
            ],
            "som": [
                {"text": "Fadlan iga caawi.", "translation": "Please help me."},
                {"text": "Cosbitaal waa inaan aadaa.", "translation": "I must go to a hospital."},
                {"text": "Xanuun baan dareemayaa.", "translation": "I feel unwell."},
            ],
        },
        IntentType.GENERAL: {
            "amh": [
                {"text": "እሺ አመሰግናለሁ", "translation": "Okay, thank you."},
                {"text": "አልገባኝም፣ በድጋሚ ንገረኝ", "translation": "I didn't understand, please repeat."},
                {"text": "አዎ እፈልጋለሁ", "translation": "Yes, I would like that."},
            ],
            "eng": [
                {"text": "Okay, thank you very much.", "translation": "እሺ፣ በጣም አመሰግናለሁ።"},
                {"text": "Could you please repeat that?", "translation": "እባክህ ልትደግምልኝ ትችላለህ?"},
                {"text": "Understood, sounds good!", "translation": "ገብቶኛል፣ ጥሩ ነው!"},
            ],
            "orm": [
                {"text": "Tole, galatoomi.", "translation": "Okay, thank you."},
                {"text": "Naaf hin galle, naaf irra deebi'i.", "translation": "I didn't understand, please repeat."},
                {"text": "Eyyee nan barbaada.", "translation": "Yes, I want that."},
            ],
            "tir": [
                {"text": "ሕራይ የቐንየለይ።", "translation": "Okay, thank you."},
                {"text": "ኣይተረድኣንን፣ ደጊምካ ንገረኒ።", "translation": "I didn't understand, please repeat."},
                {"text": "እወ እደሊ ኣለኹ።", "translation": "Yes, I want that."},
            ],
            "som": [
                {"text": "Haye, mahadsanid.", "translation": "Okay, thank you."},
                {"text": "Ma fahmin, fadlan ku celi.", "translation": "I didn't understand, please repeat."},
                {"text": "Haa waan rabaa.", "translation": "Yes, I want that."},
            ],
        },
    }

    @classmethod
    def get_suggestions(cls, intent: IntentType, tgt_lang: str) -> list[dict[str, str]]:
        """Return 3 smart quick-reply suggestion chips for the target speaker."""
        lang_key = "eng"
        if tgt_lang in ("amh", "amh_Ethi"):
            lang_key = "amh"
        elif tgt_lang in ("orm", "gaz_Latn"):
            lang_key = "orm"
        elif tgt_lang in ("tir", "tir_Ethi"):
            lang_key = "tir"
        elif tgt_lang in ("som", "som_Latn"):
            lang_key = "som"

        intent_map = cls.SUGGESTIONS_MAP.get(intent, cls.SUGGESTIONS_MAP[IntentType.GENERAL])
        return intent_map.get(lang_key, intent_map["eng"])


# ──────────────────────────────────────────────────────────────────
# 6. Unified Smart Translation Agent
# ──────────────────────────────────────────────────────────────────
@dataclass
class SmartTranslationResult:
    source_text: str
    translated_text: str
    src_lang: str
    tgt_lang: str
    intent: IntentType
    formality: str
    suggested_replies: list[dict[str, str]]
    was_idiom_match: bool = False
    context_resolved: bool = False


class SmartEngine:
    """Orchestrates multi-turn context, intent reasoning, idioms, and quick-replies."""

    @classmethod
    def process_and_translate(
        cls,
        text: str,
        src_lang: str,
        tgt_lang: str,
        session_id: str | None = None,
        formality: str = "auto",
        nmt_translator_func: Any = None,
    ) -> SmartTranslationResult:
        if not text or not text.strip():
            return SmartTranslationResult(
                source_text="",
                translated_text="",
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                intent=IntentType.GENERAL,
                formality=formality,
                suggested_replies=[],
            )

        raw_input = text.strip()
        try:
            from ai_pipeline.speech_repair import repair_stt_transcription
            raw_input = repair_stt_transcription(raw_input, src_lang)
        except Exception:
            pass

        # Step 1: Contextual Ellipsis Resolution
        context_resolved_text = SmartContextManager.resolve_contextual_ellipsis(
            raw_input, src_lang, session_id
        )
        was_context_resolved = context_resolved_text != raw_input

        # Step 2: Intent Classification
        intent = IntentClassifier.classify(context_resolved_text)

        # Step 3: Cultural Idiom De-literalization Check
        translated = CulturalIdiomEngine.match_cultural_idiom(context_resolved_text, src_lang, tgt_lang)
        was_idiom = translated is not None

        # Step 4: If not an idiom, execute standard pipeline translation
        if not translated:
            if nmt_translator_func is not None:
                translated = nmt_translator_func(context_resolved_text, src_lang, tgt_lang)
            else:
                from ai_pipeline.pipeline import TranslatorPipeline
                # fallback placeholder if called standalone
                translated = context_resolved_text

        # Step 5: Formality / Register Adjustment
        translated = FormalityController.apply_formality(translated, tgt_lang, formality)

        # Step 6: Generate Smart Follow-Up Suggestions for the interlocutor
        suggested_replies = SmartSuggestionsEngine.get_suggestions(intent, tgt_lang)

        # Step 7: Record Turn in Context History
        if session_id:
            SmartContextManager.add_turn(
                session_id=session_id,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                source_text=raw_input,
                translated_text=translated,
                intent=intent,
            )

        return SmartTranslationResult(
            source_text=context_resolved_text,
            translated_text=translated,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            intent=intent,
            formality=formality,
            suggested_replies=suggested_replies,
            was_idiom_match=was_idiom,
            context_resolved=was_context_resolved,
        )
