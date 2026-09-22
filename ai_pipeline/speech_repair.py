"""Speech-Healing and Spoken Disfluency Normalizer for Ethiopian Speech.

Repairs ASR transcriptions before translation:
1. Strips acoustic noise, laughter ('ሀ ሀ', 'haha'), stutter repetitions ('ሰላም ሰላም' -> 'ሰላም').
2. Normalizes phonetic & colloquial spoken contractions (e.g. 'መትታቃለህ' -> 'መጥተህ ታውቃለህ').
3. Normalizes Ethiopic homophone variants (ሐ/ኀ -> ሀ, ሠ -> ሰ, ዐ -> አ, ፀ -> ጸ) for dictionary consistency.
4. Completes interrupted / truncated sentences (e.g. '... የት' -> '... የት ነው?').
"""

import re

# Common spoken Amharic phonetic slurrings & contractions mapped to standard forms
AMHARIC_SPOKEN_CONTRACTIONS = [
    # Metah / Tawqaleh variants ("have you ever visited/come")
    (r"\bመትታቃለህ\b", "መጥተህ ታውቃለህ"),
    (r"\bመትታቃለሽ\b", "መጥተሽ ታውቂያለሽ"),
    (r"\bመትተው ያውቃሉ\b", "መጥተው ያውቃሉ"),
    (r"\bመተልታቅ\b", "መጥተህ ልታውቅ"),
    (r"\bመትታውቃለህ\b", "መጥተህ ታውቃለህ"),
    (r"\bመተህ\b", "መጥተህ"),
    (r"\bመተክ\b", "መጥተህ"),
    (r"\bመጥተክ\b", "መጥተህ"),
    (r"\bመታችሁ\b", "መጥታችሁ"),
    (r"\bመትቼ\b", "መጥቼ"),
    (r"\bሄድታቃለህ\b", "ሄደህ ታውቃለህ"),
    (r"\bሄደክ\b", "ሄደህ"),
    (r"\bሄድክ\b", "ሄደህ"),
    
    # Greetings & Phonetic variants
    (r"\bሳላም\b", "ሰላም"),
    (r"\bስላም\b", "ሰላም"),
    (r"\bሰላምታ\b", "ሰላም"),
    (r"\bእንደምናችሁ\b", "እንዴት ናችሁ"),
    (r"\bእንዴትናችሁ\b", "እንዴት ናችሁ"),
    (r"\bእንዴትነህ\b", "እንዴት ነህ"),
    (r"\bእንዴትነሽ\b", "እንዴት ነሽ"),
    (r"\bእንዴትነው\b", "እንዴት ነው"),
    (r"\bእንዴት\s*ነክ\b", "እንዴት ነህ"),
    (r"\bደህናነህ\b", "ደህና ነህ"),
    (r"\bደህናነሽ\b", "ደህና ነሽ"),
    (r"\bደህናነኝ\b", "ደህና ነኝ"),
    (r"\bደህና\s*ነክ\b", "ደህና ነህ"),
    (r"\bአለክ\b", "አለህ"),
    (r"\bትባላለክ\b", "ትባላለህ"),
    (r"\bነክ\b", "ነህ"),
    (r"\bስምክ\b", "ስምህ"),
    (r"\bአይደል\b", "አይደለም"),
    (r"\bእባኮትን\b", "እባክዎ"),
    (r"\bእባክዎን\b", "እባክዎ"),
    
    # Acoustic CTC word fusions & merges
    (r"\bማንት\b", "ማን ት"),
    (r"\bማንቲ\b", "ማን ት"),
    (r"\bስማንት\b", "ማን ት"),
    (r"\bእርምያስ\b", "ኤርምያስ"),
    
    # Subject-verb agreement restoration (e.g. 2nd person pronoun + hallucinated 1st person verb)
    (r"\b(አንተስ|አንተ)\s+(?:ስ)?ማን\s*ት?\s+እባላለሁ\b", r"\1 ማን ትባላለህ"),
    (r"\b(አንተስ|አንተ)\s+ማን\s+ት\s+እባላለሁ\b", r"\1 ማን ትባላለህ"),
    (r"\b(አንተስ|አንተ)\s+(?:ማን\s+)?እባላለሁ\b", r"\1 ማን ትባላለህ"),
    (r"\b(አንቺስ|አንቺ)\s+(?:ስ)?ማን\s*ት?\s+እባላለሁ\b", r"\1 ማን ትባያለሽ"),
    (r"\b(አንቺስ|አንቺ)\s+ማን\s+ት\s+እባላለሁ\b", r"\1 ማን ትባያለሽ"),
    (r"\b(አንቺስ|አንቺ)\s+(?:ማን\s+)?እባላለሁ\b", r"\1 ማን ትባያለሽ"),
    
    # Apologies and courtesies
    (r"\bይቅር\b", "ይቅርታ"),
    (r"\bአመሰግ\b", "አመሰግናለሁ"),
    (r"\bአመሰግና\b", "አመሰግናለሁ"),
    (r"\bአመሰግነ\b", "አመሰግናለሁ"),
    (r"\bአመሰግናለው\b", "አመሰግናለሁ"),
    (r"\bእፈልጋ\b", "እፈልጋለሁ"),
    (r"\bእፈልጋለ\b", "እፈልጋለሁ"),
    (r"\bደህና ሁን\b", "ደህና ሁን"),
    
    # Spoken particles & colloquial idioms
    (r"\bመናት\b", "በናትህ"),
    (r"\bምናት\b", "በናትህ"),
    (r"\bአስቢህ\s+አላውቅም\b", "አስቤ አላውቅም"),
    (r"\bአስቤህ\s+አላውቅም\b", "አስቤ አላውቅም"),
    
    # Common conversational contractions
    (r"\bአልፈልገውም\b", "አልፈልግም"),
    (r"\bአልፈልግ\b", "አልፈልግም"),
    (r"\bአልችልበትም\b", "አልችልም"),
    (r"\bአልችል\b", "አልችልም"),
    (r"\bአይመስለኝ\b", "አይመስለኝም"),
    (r"\bይመስለኛ\b", "ይመስለኛል"),
    (r"\bአላውቅ\b", "አላውቅም"),
    (r"\bአልሰማሁ\b", "አልሰማሁም"),
    (r"\bአልሰማሁም\b", "አልሰማሁም"),
]

# Amharic sentence completion rules for truncated / interrupted utterances
AMHARIC_INTERRUPTED_COMPLETIONS = [
    # Interrogatives left hanging at sentence end
    (r"\s+የት$", " የት ነው?"),
    (r"^የት$", "የት ነው?"),
    (r"\s+እንዴት$", " እንዴት ነው?"),
    (r"^እንዴት$", "እንዴት ነው?"),
    (r"\s+ስንት$", " ስንት ነው?"),
    (r"^ስንት$", "ስንት ነው?"),
    (r"\s+ማን$", " ማን ነው?"),
    (r"^ማን$", "ማን ነው?"),
    (r"\s+ምንድን$", " ምንድን ነው?"),
    (r"^ምንድን$", "ምንድን ነው?"),
    (r"\s+ለምን$", " ለምን?"),
    (r"^ለምን$", "ለምን?"),
    
    # Common verbs left cut-off at speech end
    (r"\s+መሄድ$", " መሄድ እፈልጋለሁ።"),
    (r"\s+መብላት$", " መብላት እፈልጋለሁ።"),
    (r"\s+መጠጣት$", " መጠጣት እፈልጋለሁ።"),
    (r"\s+መግዛት$", " መግዛት እፈልጋለሁ።"),
    (r"\s+መተኛት$", " መተኛት እፈልጋለሁ።"),
    (r"\s+መርዳት$", " መርዳት ትችላለህ?"),
    (r"\s+እፈልጋ$", " እፈልጋለሁ።"),
    (r"\s+እፈልጋለ$", " እፈልጋለሁ።"),
    (r"\s+ይቅር$", " ይቅርታ።"),
    (r"\s+አመሰግ$", " አመሰግናለሁ።"),
    (r"\s+አመሰግና$", " አመሰግናለሁ።"),
    (r"\s+እንደምን$", " እንደምን አለህ?"),
    
    # Interrupted social addresses at utterance tail
    (r"\s+(?:እንድ|ወንድ)[.?!።፧]*$", " ወንድሜ"),
    (r"\s+ወንድም[.?!።፧]*$", " ወንድሜ"),
    (r"\s+(?:እህት|ህት)[.?!።፧]*$", " እህቴ"),
    (r"\s+ወዳጅ[.?!።፧]*$", " ወዳጄ"),
]

# English sentence completions for interrupted speech
ENGLISH_INTERRUPTED_COMPLETIONS = [
    (r"\s+where$", " where is it?"),
    (r"^where$", "Where is it?"),
    (r"\s+how much$", " how much is it?"),
    (r"^how much$", "How much is it?"),
    (r"\s+what is$", " what is it?"),
    (r"\s+i want$", " I want this."),
    (r"\s+can you$", " can you help me?"),
]

# Afaan Oromo spoken contractions & phonetic variations
OROMO_SPOKEN_CONTRACTIONS = [
    (r"\bakkamitt\b", "akkamitti"),
    (r"\bakkamta\b", "akkam jirta"),
    (r"\bakkamtani\b", "akkam jirtu"),
    (r"\bakkam jirtani\b", "akkam jirtu"),
    (r"\bgalatoom\b", "galatoomi"),
    (r"\bgalatooma\b", "galatoomaa"),
    (r"\bbarbaad\b", "barbaada"),
    (r"\beessatt\b", "eessatti"),
    (r"\bdhiifam\b", "dhiifama"),
    (r"\bmaalo\b", "maaloo"),
    (r"\bmaalif\b", "maaliif"),
    (r"\bnagatt\b", "nagaatti"),
    (r"\bnagaa ta'i\b", "nagaatti"),
    (r"\bfayyaadhaa\b", "fayyaa dhaa"),
    (r"\bfayyummaa\b", "fayyumaa"),
    (r"\bfayummaa\b", "fayyumaa"),
    (r"\bakkam bulte\b", "akkam bulte"),
    (r"\bakkam oolte\b", "akkam oolte"),

    # Broadcast & Spoken News Contractions / ASR fusions
    (r"\bharkafuun\b", "harka fuune"),
    (r"\bharka\s*fuun\b", "harka fuune"),
    (r"\bakkamooltan\b", "akkam ooltan"),
    (r"\bakkamooltani\b", "akkam ooltan"),
    (r"\bakkamoolte\b", "akkam oolte"),
    (r"\bakkambultan\b", "akkam bultan"),
    (r"\bakkambultee\b", "akkam bulte"),
    (r"\bakkamoolta\b", "akkam oolta"),
    (r"\bodu\b", "oduu"),

    # Spoken news, political analysis, and public affairs phonetic repairs
    (r"\bgar\s+fageenya\b", "gadi fageenya"),
    (r"\bqatiilee\b", "qabxiilee"),
    (r"\btaassifamu\b", "taasifamu"),
    (r"\bins\s+baii\s+ala\s+ba'uudhaaf\b", "biyya alaa ba'uudhaaf"),
    (r"\bins\s+baii\s+ala\b", "biyya alaa"),
    (r"\bins\s+baii\b", "biyya"),
    (r"\bmugaasnesaa\b", "moggaasni isaa"),
    (r"\bmogaasnesaa\b", "moggaasni isaa"),
    (r"\bwan\s+baayyee\b", "waan baay'ee"),
    (r"\bobbo\s+j['’`]?a(?:a)?\s+mohammad\b", "Obbo Jawar Mohammed"),
    (r"\bobbo\s+j['’`]?a(?:a)?\b", "Obbo Jawaar"),
    (r"\bj['’`]?a(?:a)?\s+mohammad\b", "Jawar Mohammed"),

    # Trailing ungrounded acoustic noise/chaff to inaudible marker
    (r"\s+insootay\s+saakkea[.]?", ""),
    (r"\binsootay\b", ""),
    (r"\bsaakkea\b", ""),
]

# Tigrinya spoken contractions & phonetic variations
TIGRINYA_SPOKEN_CONTRACTIONS = [
    # Universal greetings & ASR acoustic confusions (e.g. ይሃበለይ heard as ኣበይ)
    (r"\bጥዕና\s*ኣበይ\b", "ጥዕና ይሃበለይ"),
    (r"\bጥዕናይሃበለይ\b", "ጥዕና ይሃበለይ"),
    (r"\bጥዕና\s*ይሃበላይ\b", "ጥዕና ይሃበለይ"),
    (r"\bጥዕና\s*ይሃበልና\b", "ጥዕና ይሃበለይ"),
    (r"\bከመይደኹም\b", "ከመይ ዲኹም"),
    (r"\bከመይዳኹም\b", "ከመይ ዲኹም"),
    (r"\bከመይድኻ\b", "ከመይ ዲኻ"),
    (r"\bከመይድኺ\b", "ከመይ ዲኺ"),
    (r"\bከመይዲኹም\b", "ከመይ ዲኹም"),
    (r"\bከመይዲኻ\b", "ከመይ ዲኻ"),
    (r"\bከመይዲኺ\b", "ከመይ ዲኺ"),
    (r"\bከመይለኹም\b", "ከመይ ኣለኹም"),
    (r"\bከመይለኻ\b", "ከመይ ኣለኻ"),
    (r"\bከመይለኺ\b", "ከመይ ኣለኺ"),

    # Broadcast nouns & honorific address normalization
    (r"(ዝኸበርኩም|ዝኸበርክን|ክቡራት)\s+ተመልከትና\b", r"\1 ተመልከትትና"),
    (r"\bተመልከትና\b", "ተመልከትትና"),  # Disambiguates noun 'our viewers' from verb 'we looked'

    # Word boundary / CTC fusion repair
    (r"\bሒዝናቐሪብና\b", "ሒዝና ቀሪብና"),
    (r"\bሒዝናቀሪብና\b", "ሒዝና ቀሪብና"),
    (r"\bቀሪብናኣለና\b", "ቀሪብና ኣለና"),
    (r"\bሒዝናኣለና\b", "ሒዝና ኣለና"),
    (r"\bተዳልዩኣሎ\b", "ተዳልዩ ኣሎ"),
    (r"\bተዳልያኣላ\b", "ተዳልያ ኣላ"),
    (r"\bብምቕራብ\b", "ብምቕራብ"),

    # Redundant repetitive trailing ASR loops
    (r"(ዜናታት(?:\s+\w+)*\s+ሒዝና\s+ቀሪብና\s+ኣለና)\s+ዜና\s+ብምቕራብ\b", r"\1"),

    # General conversational contractions
    (r"\bከመይኻ\b", "ከመይ ኣለኻ"),
    (r"\bከመይኺ\b", "ከመይ ኣለኺ"),
    (r"\bከመይኹም\b", "ከመይ ኣለኹም"),
    (r"\bደሓንዲኻ\b", "ደሓን ዲኻ"),
    (r"\bደሓንዲኺ\b", "ደሓን ዲኺ"),
    (r"\bደሓንዶ\b", "ደሓን ዲኻ"),
    (r"\bደሓንዶኻ\b", "ደሓን ዲኻ"),
    (r"\bየቐንየለ\b", "የቐንየለይ"),
    (r"\bየቐንየልና\b", "የቐንየልና"),
    (r"\bይቕሬ\b", "ይቕሬታ"),
    (r"\bይቅርታ\b", "ይቕሬታ"),
    (r"\bእደሊ\b", "እደሊ ኣለኹ"),
    (r"\bደሊየ\b", "እደሊ ኣለኹ"),
    (r"\bኣበይሎ\b", "ኣበይ ኣሎ"),
    (r"\bኣበይላ\b", "ኣበይ ኣላ"),
    (r"\bኣበይለው\b", "ኣበይ ኣለው"),
    (r"\bሰላምዶ\b", "ሰላም ዲኻ"),
]

# Somali spoken contractions & phonetic variations
SOMALI_SPOKEN_CONTRACTIONS = [
    (r"\biskawaran\b", "iska warran"),
    (r"\biskawarran\b", "iska warran"),
    (r"\bmahadsan\b", "mahadsanid"),
    (r"\bwaa mahadsantahay\b", "waad mahadsantahay"),
    (r"\bwaan rabaa\b", "waxaan rabaa"),
    (r"\bbiyo rabaa\b", "biyo baan rabaa"),
    (r"\bxagee\b", "xaggee"),
    (r"\bimisa\b", "immisa"),
    (r"\bnabadgelyo\b", "nabad gelyo"),
]

# Afaan Oromo completions for interrupted speech
OROMO_INTERRUPTED_COMPLETIONS = [
    (r"\s+eessa$", " eessa jira?"),
    (r"^eessa$", "Eessa jira?"),
    (r"\s+meeqa$", " meeqa?"),
    (r"^meeqa$", "Meeqa?"),
    (r"\s+akkam$", " akkam jirtu?"),
    (r"^akkam$", "Akkam jirtu?"),
    (r"\s+maaloo$", " maaloo na gargaaraa."),
    (r"\s+barbaada$", " barbaada."),
    (r"\s+barbaa$", " barbaada."),
    (r"\s+gargaa$", " na gargaaraa."),
    (r"\s+bishaan$", " bishaan barbaada."),
    (r"\s+dhiifama$", " dhiifama."),
    (r"\s+galatoomi$", " galatoomaa."),
    (r"\s+hin\s+galle$", " naaf hin galle."),
]

# Tigrinya completions for interrupted speech
TIGRINYA_INTERRUPTED_COMPLETIONS = [
    (r"\s+ኣበይ$", " ኣበይ ኣሎ?"),
    (r"^ኣበይ$", "ኣበይ ኣሎ?"),
    (r"\s+ክንዲ ምንታይ$", " ክንዲ ምንታይ እዩ?"),
    (r"^ክንዲ ምንታይ$", "ክንዲ ምንታይ እዩ?"),
    (r"\s+ከመይ$", " ከመይ ኣለኻ?"),
    (r"^ከመይ$", "ከመይ ኣለኻ?"),
    (r"\s+መን$", " መን እዩ?"),
    (r"^መን$", "መን እዩ?"),
    (r"\s+እደሊ$", " እደሊ ኣለኹ።"),
    (r"\s+ማይ$", " ማይ እደሊ ኣለኹ።"),
    (r"\s+ይቕሬታ$", " ይቕሬታ።"),
    (r"\s+የቐንየለይ$", " የቐንየለይ።"),
]

# Somali completions for interrupted speech
SOMALI_INTERRUPTED_COMPLETIONS = [
    (r"\s+xaggee$", " xaggee bay ku taal?"),
    (r"^xaggee$", "Xaggee bay ku taal?"),
    (r"\s+xagee$", " xaggee bay ku taal?"),
    (r"^xagee$", "Xaggee bay ku taal?"),
    (r"\s+immisa$", " immisa weeye?"),
    (r"^immisa$", "Immisa weeye?"),
    (r"\s+imisa$", " immisa weeye?"),
    (r"^imisa$", "Immisa weeye?"),
    (r"\s+sidee$", " sidee tahay?"),
    (r"^sidee$", "Sidee tahay?"),
    (r"\s+maxay$", " maxay tahay?"),
    (r"^maxay$", "Maxay tahay?"),
    (r"\s+rabaa$", " rabaa."),
    (r"\s+biyo$", " biyo baan rabaa."),
    (r"\s+fadlan$", " fadlan iga caawi."),
    (r"\s+mahadsanid$", " mahadsanid."),
]


class SpeechRepair:
    """Intelligent pre-translation repair engine for spoken Ethiopian languages."""

    @classmethod
    def clean_noise_and_stutter(cls, text: str) -> str:
        """Strip laughter, filler sounds, and consecutive duplicate words (stutter)."""
        if not text:
            return ""

        cleaned = text.strip()

        # 1. Remove Ge'ez laughter patterns: 'ሀ ሀ', 'ሃ ሃ', 'ሆ ሆ', 'ሄ ሄ', 'ሃሃ', etc.
        cleaned = re.sub(r"(?:^|\s)(?:[ሀሃሆሄ]\s*)+(?=$|\s)", " ", cleaned)

        # Latin laughter patterns: 'haha', 'hahaha', 'hehe', 'ha ha', 'he he'
        cleaned = re.sub(r"(?i)\b(?:ha|he|ah)+(?:\s*(?:ha|he|ah)+)*\b", " ", cleaned)

        # 2. Remove filler hesitation tokens: 'እ...', 'አ...', 'um', 'uh', 'er'
        cleaned = re.sub(r"(?:^|\s)[እአ]+(?:\.{2,})?(?=$|\s)", " ", cleaned)
        cleaned = re.sub(r"(?i)\b(?:um+|uh+|er+)\b", " ", cleaned)

        # 3. Deduplicate consecutive repeated words (acoustic stuttering: e.g. 'ሰላም ሰላም' -> 'ሰላም')
        cleaned = re.sub(r"([^\s\d\W]+)(?:\s+\1\b)+", r"\1", cleaned, flags=re.UNICODE)

        # 4. Collapse extra whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @classmethod
    def normalize_ethiopic_homophones(cls, text: str) -> str:
        """Canonicalize homophonous Ge'ez letters so orthographic variants match dictionaries."""
        if not text:
            return ""
        # ሐ -> ሀ, ኀ -> ሀ
        res = re.sub(r"[ሐሑሒሓሔሕሖ]", lambda m: chr(ord(m.group(0)) - ord('ሐ') + ord('ሀ')), text)
        res = re.sub(r"[ኀኁኂኃኄኅኆ]", lambda m: chr(ord(m.group(0)) - ord('ኀ') + ord('ሀ')), res)
        # ሠ -> ሰ
        res = re.sub(r"[ሠሡሢሣሤሥሦ]", lambda m: chr(ord(m.group(0)) - ord('ሠ') + ord('ሰ')), res)
        # ዐ -> አ
        res = re.sub(r"[ዐዑዒዓዔዕዖ]", lambda m: chr(ord(m.group(0)) - ord('ዐ') + ord('አ')), res)
        # ፀ -> ጸ
        res = re.sub(r"[ፀፁፂፃፄፅፆ]", lambda m: chr(ord(m.group(0)) - ord('ፀ') + ord('ጸ')), res)
        return res

    @classmethod
    def expand_spoken_contractions(cls, text: str, lang_code: str) -> str:
        """Expand spoken phonetics and colloquial slurrings into grammatical forms."""
        if not text:
            return ""

        normalized = text

        if lang_code in ("amh", "amh_Ethi"):
            for pattern, replacement in AMHARIC_SPOKEN_CONTRACTIONS:
                normalized = re.sub(pattern, replacement, normalized)
        elif lang_code in ("orm", "gaz_Latn"):
            for pattern, replacement in OROMO_SPOKEN_CONTRACTIONS:
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        elif lang_code in ("tir", "tir_Ethi"):
            for pattern, replacement in TIGRINYA_SPOKEN_CONTRACTIONS:
                normalized = re.sub(pattern, replacement, normalized)
        elif lang_code in ("som", "som_Latn"):
            for pattern, replacement in SOMALI_SPOKEN_CONTRACTIONS:
                normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

        return normalized

    @classmethod
    def complete_interrupted_speech(cls, text: str, lang_code: str) -> str:
        """Heuristically complete phrases cut off mid-thought due to audio interruption."""
        if not text:
            return ""

        result = text.rstrip()

        if lang_code in ("amh", "amh_Ethi"):
            for pattern, completion in AMHARIC_INTERRUPTED_COMPLETIONS:
                if re.search(pattern, result):
                    result = re.sub(pattern, completion, result)
                    break

        elif lang_code in ("eng", "eng_Latn"):
            for pattern, completion in ENGLISH_INTERRUPTED_COMPLETIONS:
                if re.search(pattern, result, flags=re.IGNORECASE):
                    result = re.sub(pattern, completion, result, flags=re.IGNORECASE)
                    break

        elif lang_code in ("orm", "gaz_Latn"):
            for pattern, completion in OROMO_INTERRUPTED_COMPLETIONS:
                if re.search(pattern, result, flags=re.IGNORECASE):
                    result = re.sub(pattern, completion, result, flags=re.IGNORECASE)
                    break

        elif lang_code in ("tir", "tir_Ethi"):
            for pattern, completion in TIGRINYA_INTERRUPTED_COMPLETIONS:
                if re.search(pattern, result):
                    result = re.sub(pattern, completion, result)
                    break

        elif lang_code in ("som", "som_Latn"):
            for pattern, completion in SOMALI_INTERRUPTED_COMPLETIONS:
                if re.search(pattern, result, flags=re.IGNORECASE):
                    result = re.sub(pattern, completion, result, flags=re.IGNORECASE)
                    break

        return result.strip()

    @classmethod
    def repair(cls, raw_text: str, lang_code: str) -> str:
        """Execute full speech repair pipeline: clean noise -> expand slurs -> complete thought."""
        if not raw_text or not raw_text.strip():
            return ""

        # Step 1: Clean acoustic noise, laughter, and stutters
        text = cls.clean_noise_and_stutter(raw_text)

        # Step 2: Expand spoken contractions & dialectal phonetic variations
        text = cls.expand_spoken_contractions(text, lang_code)

        # Step 3: Complete truncated or interrupted utterances
        text = cls.complete_interrupted_speech(text, lang_code)

        # Step 4: Restore natural punctuation and clause boundaries for unpunctuated ASR
        text = cls.restore_spoken_sentence_boundaries(text, lang_code)

        return text

    @classmethod
    def restore_spoken_sentence_boundaries(cls, text: str, lang_code: str) -> str:
        """Add punctuation boundaries for spoken speech that ASR models output without punctuation."""
        if not text:
            return ""

        s = text
        if lang_code in ("amh", "amh_Ethi"):
            # Colloquial particle 'በናትህ' after a question clause forms a single unit: "እንዴት ነው በናትህ?"
            s = re.sub(r"(እንዴት ነው|እንዴት ነህ|እንዴት ነሽ|እንዴት ናችሁ|ስንት ነው|የት ነው|ምንድን ነው|ምን ታስባለህ)\s+(በናትህ|በናትሽ|በናታችሁ)\s+(ይህ|ይሄ|እኔ|አንተ|እሱ|እሷ|ግን|ደግሞ)", r"\1 \2? \3", s)
            s = re.sub(r"(በናትህ|በናትሽ|በናታችሁ)\s+(ይህ|ይሄ|እኔ|አንተ|እባክህ|ስለ|ደግሞ)", r"\1? \2", s)
            s = re.sub(r"(እንዴት ነው|እንዴት ነህ|እንዴት ነሽ|እንዴት ናችሁ|ስንት ነው|የት ነው|ምንድን ነው|ምን ታስባለህ)\s+(ይህ|ይሄ|እኔ|አንተ|እሱ|እሷ|ግን|ደግሞ)", r"\1? \2", s)
            
            # Exclamations and descriptive completions
            s = re.sub(r"(ደስ የሚል ሀገር ነው|ደስ ይላል)\s+(እኔ|አንተ|ግን|ይህ|ይሄ)", r"\1! \2", s)
            
            # Sentence completions before new clause
            s = re.sub(r"(አላውቅም|አልፈልግም|አይደለም|አመሰግናለሁ|አመሰግናለው)\s+(አንተ|እኔ|ግን|ደግሞ|ይህ|ይሄ|ስለ)", r"\1። \2", s)
            
            # Greeting phrases followed by introduction or statement
            s = re.sub(r"(ሰላም ነው|ሰላም\s+እንዴት ነህ|ሰላም\s+እንዴት ነሽ|ሰላም\s+እንዴት ናችሁ|ሰላም\s+እንዴት ነው|እንዴት ነህ|እንዴት ነሽ|እንዴት ናችሁ|እንዴት ነው)\s+(እኔ|እኛ|አንተ|አንቺ|ይህ|ይሄ|ስሜ|እባክህ|ዛሬ|አሁን)", r"\1? \2", s)
            s = re.sub(r"^ሰላም\s+(እንዴት ነህ|እንዴት ነሽ|እንዴት ናችሁ|እንዴት ነው)$", r"ሰላም \1?", s)
            
            # Self-introductions & declarative predicates before transition: "እኔ ... እባላለሁ። አንተስ..."
            s = re.sub(r"(እባላለሁ|ይባላል|ተባልኩ|ነኝ|ነው|ነበር)\s+(አንተስ|አንቺስ|እናንተስ|እሱስ|እሷስ|እሱም|እሷም|አንተ|አንቺ|ግን|ደግሞ)", r"\1። \2", s)
            
            # Terminal punctuation if missing
            if s and not s[-1] in ".?!:;፣፧፨\n":
                if re.search(r"(ምን ታስባለህ|እንዴት ነው|እንዴት ነህ|እንዴት ነሽ|እንዴት ናችሁ|የት ነው|ስንት ነው|ለምን|ምንድነው|ማን ትባላለህ|ማን ትባያለሽ|ስምህ ማን ነው|ስምሽ ማን ነው|ማን ነው)(?:\s+(?:ወንድሜ|እህቴ|ወዳጄ|ጓደኛዬ))?$", s):
                    s += "?"
                else:
                    s += "።"

        elif lang_code in ("orm", "gaz_Latn"):
            # Oromo clause boundaries & question marks
            s = re.sub(r"(?i)\b(akkam jirta|akkam jirtu|akkamitti|eessa jira|meeqa|eenyu|maaliif)\b(?!\?)", r"\1?", s)
            s = re.sub(r"(?i)(akkam|nagaa dhaa|fayyaa dhaa)\s+(akkam jirta|fayyaa dhaa|hospitaalichi|maaloo)", r"\1! \2", s)
            s = re.sub(r"(?i)(galatoomaa|galatoomi|nagaatti|dhiifama)\s+([A-Za-z])", r"\1. \2", s)
            s = re.sub(r"\.{2,}", ".", s)
            if s and not s[-1] in ".?!:;\n":
                if re.search(r"(?i)\b(akkam|eessa|meeqa|eenyu|maaliif|dhaa|jirta|jirtu)\??$", s):
                    s += "?"
                else:
                    s += "."

        elif lang_code in ("tir", "tir_Ethi"):
            # Normalize Ethiopic word dividers/colons (:: or ፡) to standard punctuation
            s = re.sub(r"::\s*", "። ", s)
            s = re.sub(r"፡+", " ", s)

            # Standard conversational clause boundaries
            s = re.sub(r"(ከመይ ኣለኻ|ከመይ ኣለኺ|ከመይ ኣለኹም|ከመይ ዲኹም|ከመይ ዲኻ|ከመይ ዲኺ|ኣበይ ኣሎ|ኣበይ ኣላ|ክንዲ ምንታይ|መን እዩ|ስለምንታይ|ደሓንዶ|ደሓን ዲኻ)\s+(እዚ|እቲ|ኣነ|ንስኻ|ንስኺ|ግን|ደግሞ|ሎሚ)", r"\1? \2", s)
            s = re.sub(r"(ሰላም|ሰላም እዩ)\s+(ከመይ ኣለኻ|ከመይ ኣለኺ|ከመይ ዲኹም|ደሓንዶ|ደሓን ዲኻ)", r"\1! \2", s)
            s = re.sub(r"(እደሊ ኣለኹ|የቐንየለይ|ደሓን|እዩ|ኣይኮነን|ቀሪብና ኣለና)\s+(ኣነ|ንስኻ|ንስኺ|ግን|እዚ|ደግሞ|ሎሚ)", r"\1። \2", s)
            # Clean up consecutive punctuation and trailing punctuation
            s = re.sub(r"[።\.\s]+$", "", s)
            if s:
                if re.search(r"(ከመይ ኣለኻ|ከመይ ኣለኺ|ከመይ ኣለኹም|ከመይ ዲኹም|ከመይ ዲኻ|ከመይ ዲኺ|ኣበይ ኣሎ|ክንዲ ምንታይ|መን እዩ|ደሓንዶ|ደሓን ዲኻ|ስለምንታይ)$", s):
                    s += "?"
                else:
                    s += "።"

        elif lang_code in ("som", "som_Latn"):
            # Somali clause boundaries & punctuation
            s = re.sub(r"(?i)\b(sidee tahay|sidee tihiin|iska warran|xaggee bay ku taal|immisa weeye|maxay tahay|waayo)\b(?!\?)", r"\1?", s)
            s = re.sub(r"(?i)(iska warran|nabad)\s+(sidee tahay|subax wanaagsan|galab wanaagsan)", r"\1! \2", s)
            s = re.sub(r"(?i)(mahadsanid|nabad gelyo|waan fiicanahay)\s+([A-Za-z])", r"\1. \2", s)
            if s and not s[-1] in ".?!:;\n":
                if re.search(r"(?i)\b(sidee|xaggee|xagee|immisa|imisa|maxay|waayo|miyaa)\??$", s):
                    s += "?"
                else:
                    s += "."

        elif lang_code in ("eng", "eng_Latn"):
            if s and not s[-1] in ".?!:;\n":
                if re.search(r"(?i)\b(what|where|who|when|why|how|are you|is it|can you)\b", s):
                    s += "?"
                else:
                    s += "."

        return s


def repair_stt_transcription(raw_text: str, lang_code: str) -> str:
    """Convenience functional wrapper for SpeechRepair.repair."""
    return SpeechRepair.repair(raw_text, lang_code)

