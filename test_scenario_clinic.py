"""
Scenario 1 Verification: In a Clinic (Medical & Health).
"""

import sys
from pathlib import Path

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_pipeline.smart_engine import IntentClassifier, IntentType, CulturalIdiomEngine, SmartSuggestionsEngine
from ai_pipeline.translation_memory import TranslationMemory


def test_clinic_scenario():
    print("\n==================================================")
    print("TESTING SCENARIO 1: IN A CLINIC (MEDICAL & HEALTH)")
    print("==================================================")

    # 1. Intent Classification in all 5 languages
    test_cases = [
        ("orm", "dhiibbaa dhiigaa koo safaruu qabdu", IntentType.MEDICAL),
        ("amh", "የት አካባቢ ያመዎታል የደም ምርመራ ያስፈልግዎታል", IntentType.MEDICAL),
        ("tir", "ኣፍ-ልበይ ኣበርቲዑ የሕምመኒ ኣሎ", IntentType.MEDICAL),
        ("som", "Waa inaan cabbiraa cadaadiska dhiiggaaga", IntentType.MEDICAL),
        ("eng", "Where is the laboratory for the blood test?", IntentType.MEDICAL),
    ]

    for lang, text, expected in test_cases:
        detected = IntentClassifier.classify(text)
        print(f"[{lang.upper()}] '{text}' => Intent: {detected.value}")
        assert detected == expected, f"Expected {expected}, got {detected}"
    print("✓ Intent classification in all 5 languages PASSED!")

    # 2. Medical Healing Idioms
    idiom_cases = [
        ("amh", "እግዜር ይማርህ", "eng", "May God grant you health and recovery"),
        ("orm", "fayyuu kee haa ta'u", "amh", "እግዜር ይማርህ"),
        ("tir", "ፈጣሪ ይምሓርካ", "amh", "እግዜር ይማርህ"),
        ("som", "alla ha ku caafiyo", "amh", "እግዜር ይማርህ"),
    ]

    for src, text, tgt, expected_substr in idiom_cases:
        matched = CulturalIdiomEngine.match_cultural_idiom(text, src, tgt)
        print(f"Idiom [{src}->{tgt}] '{text}' => '{matched}'")
        assert matched is not None, f"Failed to match idiom for '{text}'"
        assert expected_substr in matched, f"Expected '{expected_substr}' in '{matched}'"
    print("✓ Clinical healing idioms PASSED!")

    # 3. Verified TM Dialogue Hits
    tm = TranslationMemory.get_instance()
    
    # Doctor instruction: orm -> tir
    m1 = tm.lookup("Kiniina tokko sa'aatii saddeet saddeetiin bishaan baay'ee wajjin liqimsaa.", "orm", "tir")
    assert m1 is not None, "Failed to match dosage orm->tir"
    print(f"Dosage [ORM->TIR]: '{m1.target_text}' (score={m1.score})")
    assert "ኪኒን" in m1.target_text

    # Patient symptom: som -> amh
    m2 = tm.lookup("Laabta ayaa aad ii xanuunaysa, neefsashaduna way igu adagtahay.", "som", "amh")
    assert m2 is not None, "Failed to match symptom som->amh"
    print(f"Symptom [SOM->AMH]: '{m2.target_text}' (score={m2.score})")
    assert "ደረቴን" in m2.target_text

    # Doctor lab query: tir -> eng
    m3 = tm.lookup("ናይ ደም መርመራ ዝግበረሉ ክፍሊ ላቦራቶሪ ኣበይ ኣሎ?", "tir", "eng")
    assert m3 is not None, "Failed to match lab query tir->eng"
    print(f"Lab Query [TIR->ENG]: '{m3.target_text}' (score={m3.score})")
    assert "laboratory" in m3.target_text.lower()

    print("✓ Clinical TM dialogue hits PASSED!")

    # 4. Contextual Quick Replies
    for lang in ["amh", "orm", "tir", "som", "eng"]:
        replies = SmartSuggestionsEngine.get_suggestions(IntentType.MEDICAL, lang)
        print(f"Quick replies for [{lang}]: {len(replies)} suggestions")
        assert len(replies) >= 3
    print("✓ Clinical Quick Replies in all 5 languages PASSED!")

    print("\n==================================================")
    print("SCENARIO 1 (CLINIC) VERIFIED 100% SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    test_clinic_scenario()
