"""
Automated Verification Suite for Scenario 7: School & University Administration.

Validates:
1. Multi-lingual intent recognition (orm, amh, tir, som, eng) -> education_academic
2. Cultural education idioms (ትምህርትህ ያብራህ, barumsi kee siif haa ifu, ትምህርትኻ የብርሃልካ, waxbarashadaadu ha kuu iftiinto, እውቀት ይክፈትህ)
3. Full Translation Memory retrieval hits across language pairs
4. Contextual quick-reply suggestions in all 5 target languages
"""

import sys
from pathlib import Path

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_pipeline.smart_engine import (
    IntentClassifier,
    IntentType,
    CulturalIdiomEngine,
    SmartSuggestionsEngine,
)
from ai_pipeline.translation_memory import TranslationMemory


def test_school_intent():
    print("\n--- 1. Testing School & Education Intent Classification ---")
    test_cases = [
        ("orm", "Akkam jirtu, biiroo rejistiraaraa fi kaffaltii barumsaa eessatti argadha?", IntentType.EDUCATION),
        ("amh", "የዲግሪ ምስክር ወረቀቴን እና ለኤምባሲ የሚሆን ይፋዊ የትራንስክሪፕት ቅጅ እፈልጋለሁ።", IntentType.EDUCATION),
        ("tir", "ናይዚ ሰሚስተር ትምህርትታት ንምውሳኽ ወይ ንምስራዝ ናይ ኣድ-ድሮፕ ግዜ ክሳብ መዓስ እዩ?", IntentType.EDUCATION),
        ("som", "Jadwalka imtixaanka ugu dambeeya iyo qolalka imtixaanka xaggee lagu dhajiyaa?", IntentType.EDUCATION),
        ("eng", "Where is the dormitory room and bed allocation handled for newly admitted students?", IntentType.EDUCATION),
    ]

    for lang, text, expected in test_cases:
        intent = IntentClassifier.classify(text)
        print(f"[{lang.upper()}] '{text}' => Intent: {intent.value}")
        assert intent == expected, f"Expected {expected}, got {intent} for '{text}' ({lang})"
    print("✓ School & Education intent classification in all 5 languages PASSED!")


def test_school_idioms():
    print("\n--- 2. Testing Education & Academic Idioms ---")
    # Amharic -> English: ትምህርትህ ያብራህ
    eng_res = CulturalIdiomEngine.match_cultural_idiom("ትምህርትህ ያብራህ", src_lang="amh", tgt_lang="eng")
    print(f"Idiom [amh->eng] 'ትምህርትህ ያብራህ' => '{eng_res}'")
    assert eng_res is not None and "education" in eng_res.lower()

    # Oromo -> Amharic: barumsi kee siif haa ifu
    amh_from_orm = CulturalIdiomEngine.match_cultural_idiom("barumsi kee siif haa ifu", src_lang="orm", tgt_lang="amh")
    print(f"Idiom [orm->amh] 'barumsi kee siif haa ifu' => '{amh_from_orm}'")
    assert amh_from_orm is not None and "ትምህርትህ" in amh_from_orm

    # Tigrinya -> Amharic: ትምህርትኻ የብርሃልካ
    amh_from_tir = CulturalIdiomEngine.match_cultural_idiom("ትምህርትኻ የብርሃልካ", src_lang="tir", tgt_lang="amh")
    print(f"Idiom [tir->amh] 'ትምህርትኻ የብርሃልካ' => '{amh_from_tir}'")
    assert amh_from_tir is not None and "ትምህርትህ" in amh_from_tir

    # Somali -> Amharic: waxbarashadaadu ha kuu iftiinto
    amh_from_som = CulturalIdiomEngine.match_cultural_idiom("waxbarashadaadu ha kuu iftiinto", src_lang="som", tgt_lang="amh")
    print(f"Idiom [som->amh] 'waxbarashadaadu ha kuu iftiinto' => '{amh_from_som}'")
    assert amh_from_som is not None and "ትምህርትህ" in amh_from_som

    # Amharic -> Tigrinya: ትምህርትህ ያብራህ
    tir_from_amh = CulturalIdiomEngine.match_cultural_idiom("ትምህርትህ ያብራህ", src_lang="amh", tgt_lang="tir")
    print(f"Idiom [amh->tir] 'ትምህርትህ ያብራህ' => '{tir_from_amh}'")
    assert tir_from_amh is not None and "ትምህርትኻ" in tir_from_amh

    print("✓ Education & Academic idioms PASSED!")


def test_school_tm_hits():
    print("\n--- 3. Testing School TM Dialogue Hits ---")
    tm = TranslationMemory.get_instance()

    # Turn 1: Registrar and tuition payment location (SOM -> AMH)
    src_som = "Nabadeey, xaggee baan ka heli karaa xafiiska diiwaangeliyaha iyo daaqadda lacag-bixinta?"
    match_amh = tm.lookup(src_som, src_lang="som", tgt_lang="amh")
    assert match_amh is not None, f"TM miss for SOM->AMH: '{src_som}'"
    print(f"Registrar [SOM->AMH]: '{match_amh.target_text}' (score={match_amh.score:.2f})")
    assert "ሬጅስትራር" in match_amh.target_text

    # Turn 4: Cost sharing and clearance (ORM -> TIR)
    src_orm = "Tiraanskiriiptii ifaa fudhachuuf waraqaa qulqullinaa fi ragaa kaffaltii baasii qooddachuu dhiheessuu qabdu."
    match_tir = tm.lookup(src_orm, src_lang="orm", tgt_lang="tir")
    assert match_tir is not None, f"TM miss for ORM->TIR: '{src_orm}'"
    print(f"Clearance [ORM->TIR]: '{match_tir.target_text}' (score={match_tir.score:.2f})")
    assert "ክሊራንስ" in match_tir.target_text

    # Turn 8: Add-drop deadline (ENG -> ORM)
    src_eng = "Next Friday at five PM course registration and add-drop will be completely closed."
    match_orm = tm.lookup(src_eng, src_lang="eng", tgt_lang="orm")
    assert match_orm is not None, f"TM miss for ENG->ORM: '{src_eng}'"
    print(f"Add-Drop [ENG->ORM]: '{match_orm.target_text}' (score={match_orm.score:.2f})")
    assert "add-drop" in match_orm.target_text.lower()

    # Turn 12: Dorm room key and mattress (TIR -> ENG)
    src_tir = "ናብ ናይ ተመሃሮ ኣገልግሎት ቤት ጽሕፈት ናይ ምዝገባ ወረቐትኩም ሒዝኩም ብምኻድ መፍትሕ ክፍሊን ፍራሽን ተረከቡ።"
    match_eng = tm.lookup(src_tir, src_lang="tir", tgt_lang="eng")
    assert match_eng is not None, f"TM miss for TIR->ENG: '{src_tir}'"
    print(f"Dorm Key [TIR->ENG]: '{match_eng.target_text}' (score={match_eng.score:.2f})")
    assert "mattress" in match_eng.target_text.lower()

    # Turn 14: Commencement gown and blessing (AMH -> SOM)
    src_amh = "ከዋናው አዳራሽ ፊት ለፊት ጋውኑን ውሰዱ፣ ትምህርታችሁ ያብራችሁ፣ እንኳን ደስ አላችሁ!"
    match_som = tm.lookup(src_amh, src_lang="amh", tgt_lang="som")
    assert match_som is not None, f"TM miss for AMH->SOM: '{src_amh}'"
    print(f"Graduation [AMH->SOM]: '{match_som.target_text}' (score={match_som.score:.2f})")
    assert "hambalyo" in match_som.target_text.lower()

    print("✓ School TM dialogue hits PASSED!")


def test_school_quick_replies():
    print("\n--- 4. Testing School Quick Replies in All 5 Languages ---")
    langs = ["amh", "orm", "tir", "som", "eng"]
    for l in langs:
        replies = SmartSuggestionsEngine.get_suggestions(IntentType.EDUCATION, l)
        assert len(replies) >= 3, f"Not enough suggestions for {l}"
        print(f"Quick replies for [{l}]: {len(replies)} suggestions")
        for r in replies:
            assert "text" in r and "translation" in r
    print("✓ School Quick Replies in all 5 languages PASSED!")


if __name__ == "__main__":
    print("=" * 50)
    print("TESTING SCENARIO 7: SCHOOL & UNIVERSITY ADMINISTRATION")
    print("=" * 50)
    test_school_intent()
    test_school_idioms()
    test_school_tm_hits()
    test_school_quick_replies()
    print("\n" + "=" * 50)
    print("SCENARIO 7 (SCHOOL & UNIVERSITY) VERIFIED 100% SUCCESSFULLY!")
    print("=" * 50)
