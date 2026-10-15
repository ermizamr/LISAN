import sys
import os
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import ai_pipeline.speech_repair as sr_mod
from ai_pipeline.speech_repair import SpeechRepair
from ai_pipeline.pipeline import NLLB200Translator

# Add the new patterns temporarily for testing
sr_mod.AMHARIC_SPOKEN_CONTRACTIONS = [
    (r"\bአመሰግነ\b", "አመሰግናለሁ"),
    (r"\bአመሰግናለው\b", "አመሰግናለሁ"),
    (r"\bመናት\b", "በናትህ"),
    (r"\bምናት\b", "በናትህ"),
    (r"\bአስቢህ\s+አላውቅም\b", "አስቤ አላውቅም"),
    (r"\bአስቤህ\s+አላውቅም\b", "አስቤ አላውቅም"),
] + sr_mod.AMHARIC_SPOKEN_CONTRACTIONS

def restore_spoken_sentence_boundaries(text: str) -> str:
    s = text
    s = re.sub(r"(በናትህ|በናትሽ)\s+(ይህ|ይሄ|እኔ|አንተ|እባክህ|ስለ|ደግሞ)", r"\1? \2", s)
    s = re.sub(r"(እንዴት ነው|እንዴት ነህ|እንዴት ነሽ|እንዴት ናችሁ|ስንት ነው|የት ነው|ምንድን ነው|ምን ታስባለህ)\s+(ይህ|ይሄ|እኔ|አንተ|እሱ|እሷ|ግን|ደግሞ|በናትህ)", r"\1? \2", s)
    s = re.sub(r"(ደስ የሚል ሀገር ነው|ደስ ይላል)\s+(እኔ|አንተ|ግን|ይህ|ይሄ)", r"\1! \2", s)
    s = re.sub(r"(አላውቅም|አልፈልግም|አይደለም|አመሰግናለሁ|አመሰግናለው)\s+(አንተ|እኔ|ግን|ደግሞ|ይህ|ይሄ|ስለ)", r"\1። \2", s)
    s = re.sub(r"(ሰላም ነው|ሰላም)\s+(እንዴት ነህ|እንዴት ነሽ|እንዴት ናችሁ|እንዴት ነው)", r"\1! \2", s)
    if s and not s[-1] in ".?!:;፣፧፨\n":
        if re.search(r"(ምን ታስባለህ|እንዴት ነው|እንዴት ነህ|እንዴት ነሽ|እንዴት ናችሁ|የት ነው|ስንት ነው|ለምን|ምንድነው)$", s):
            s += "?"
        else:
            s += "።"
    return s

translator = NLLB200Translator()
translator.load()

test_cases = [
    ("Test 1", "ሰላም እንዴት ነው"),
    ("Test 2", "ሰላም ነው እንዴት ነህ እኔ በጣም ደህና ነኝ አመሰግነ"),
    ("Test 3", "ሀገሩ እንዴት ነው መናት ይህ ሀገር በጣም ደስ የሚል ሀገር ነው እኔ ይሄ ሀገር በጣም ደስ ይላል ብዬ አስቢህ አላውቅም አንተ ግን ስለዚች ሀገር ስለዚህ ሀገር ስለዚህ ሀገርና ስለ እነዚህ ሀገራት ምን ታስባለህ"),
]

for label, raw in test_cases:
    print(f"\n=== {label} ===")
    print("Raw input:       ", raw)
    repaired = SpeechRepair.repair(raw, "amh")
    punctuated = restore_spoken_sentence_boundaries(repaired)
    print("Repaired & Punct:", punctuated)
    translated = translator.translate(punctuated, "amh_Ethi", "eng_Latn")
    print("Translated:      ", translated)
