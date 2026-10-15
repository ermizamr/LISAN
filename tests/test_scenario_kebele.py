"""
Automated Verification Suite for Scenario 5: Kebele / Government Administrative Office.

Validates:
1. Multi-lingual intent recognition (orm, amh, tir, som, eng) -> civic_governance
2. Cultural civic idioms (ጉዳይህ ይፈጸም, dhimmi kee haa xumuramu, ጉዳይካ ይፈጸም, arrintaadu ha fulo, ስራህ ይቅናህ)
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


def test_kebele_intent():
    print("\n--- 1. Testing Kebele / Civic Intent Classification ---")
    test_cases = [
        ("orm", "Waraqaan eenyummaa gandaa koo waan jalaa badeef haaromsuun barbaada", IntentType.CIVIC_GOV),
        ("amh", "አዲሱ የቀበሌ መታወቂያ ካርድ ተዘጋጅቶ ለመድረስ ስንት የስራ ቀናት ይወስዳል?", IntentType.CIVIC_GOV),
        ("tir", "ኣብዚ ናይ ውዕል ደብዳበ ናይ ቀበሌ ማሕተምን ፊርማን ከተዕርፉለይ ትኽእሉዶ?", IntentType.CIVIC_GOV),
        ("som", "Xaggee baan ku bixiyaa lacagta adeegga dawladda hoose, ma heli karaa rasiid rasmi ah?", IntentType.CIVIC_GOV),
        ("eng", "What documents are required to renew my expired resident identification card?", IntentType.CIVIC_GOV),
    ]

    for lang, text, expected in test_cases:
        intent = IntentClassifier.classify(text)
        print(f"[{lang.upper()}] '{text}' => Intent: {intent.value}")
        assert intent == expected, f"Expected {expected}, got {intent} for '{text}' ({lang})"
    print("✓ Kebele / Civic intent classification in all 5 languages PASSED!")


def test_kebele_idioms():
    print("\n--- 2. Testing Kebele & Civic Idioms ---")
    # Amharic -> English: ጉዳይህ ይፈጸም
    eng_res = CulturalIdiomEngine.match_cultural_idiom("ጉዳይህ ይፈጸም", src_lang="amh", tgt_lang="eng")
    print(f"Idiom [amh->eng] 'ጉዳይህ ይፈጸም' => '{eng_res}'")
    assert eng_res is not None and "administrative" in eng_res.lower()

    # Oromo -> Amharic: dhimmi kee haa xumuramu
    amh_from_orm = CulturalIdiomEngine.match_cultural_idiom("dhimmi kee haa xumuramu", src_lang="orm", tgt_lang="amh")
    print(f"Idiom [orm->amh] 'dhimmi kee haa xumuramu' => '{amh_from_orm}'")
    assert amh_from_orm is not None and "ጉዳይህ" in amh_from_orm

    # Tigrinya -> Amharic: ጉዳይካ ይፈጸም
    amh_from_tir = CulturalIdiomEngine.match_cultural_idiom("ጉዳይካ ይፈጸም", src_lang="tir", tgt_lang="amh")
    print(f"Idiom [tir->amh] 'ጉዳይካ ይፈጸም' => '{amh_from_tir}'")
    assert amh_from_tir is not None and "ጉዳይህ" in amh_from_tir

    # Somali -> Amharic: arrintaadu ha fulo
    amh_from_som = CulturalIdiomEngine.match_cultural_idiom("arrintaadu ha fulo", src_lang="som", tgt_lang="amh")
    print(f"Idiom [som->amh] 'arrintaadu ha fulo' => '{amh_from_som}'")
    assert amh_from_som is not None and "ጉዳይህ" in amh_from_som

    # Work success: Amharic -> Tigrinya: ስራህ ይቅናህ
    tir_from_amh = CulturalIdiomEngine.match_cultural_idiom("ስራህ ይቅናህ", src_lang="amh", tgt_lang="tir")
    print(f"Idiom [amh->tir] 'ስራህ ይቅናህ' => '{tir_from_amh}'")
    assert tir_from_amh is not None and "ስራሕካ" in tir_from_amh

    print("✓ Kebele & Civic idioms PASSED!")


def test_kebele_tm_hits():
    print("\n--- 3. Testing Kebele TM Dialogue Hits ---")
    tm = TranslationMemory.get_instance()

    # Turn 3: Expired ID renewal documents (SOM -> AMH)
    src_som = "Waa maxay dukumentiyada looga baahan yahay cusboonaysiinta kaarkayga aqoonsiga ee dhacay?"
    match_amh = tm.lookup(src_som, src_lang="som", tgt_lang="amh")
    assert match_amh is not None, f"TM miss for SOM->AMH: '{src_som}'"
    print(f"ID Docs [SOM->AMH]: '{match_amh.target_text}' (score={match_amh.score:.2f})")
    assert "መታወቂያ" in match_amh.target_text

    # Turn 5: Fayda national digital ID (ORM -> TIR)
    src_orm = "Sanadoota hunda fi lakkoofsa waraqaa eenyummaa dijitaalaa biyyoolessaa Fayidaa koo qabadheen dhufe."
    match_tir = tm.lookup(src_orm, src_lang="orm", tgt_lang="tir")
    assert match_tir is not None, f"TM miss for ORM->TIR: '{src_orm}'"
    print(f"Fayda ID [ORM->TIR]: '{match_tir.target_text}' (score={match_tir.score:.2f})")
    assert "ፋይዳ" in match_tir.target_text

    # Turn 7: Biometric thumb scanner (ENG -> ORM)
    src_eng = "Very good, please place your thumb on the digital biometric scanner for verification."
    match_orm = tm.lookup(src_eng, src_lang="eng", tgt_lang="orm")
    assert match_orm is not None, f"TM miss for ENG->ORM: '{src_eng}'"
    print(f"Biometric [ENG->ORM]: '{match_orm.target_text}' (score={match_orm.score:.2f})")
    assert "ashaaraa" in match_orm.target_text.lower()

    # Turn 9: Birth certificate from vital events (TIR -> ENG)
    src_tir = "ከምኡ'ውን ነቲ ሓዲሽ እተወልደ ቈልዓይ ናይ ልደት ምስክር ወረቐት ካብ ቤት ጽሕፈት ወሳኒ ኲነታት ክወስድ እደሊ ኣለኹ።"
    match_eng = tm.lookup(src_tir, src_lang="tir", tgt_lang="eng")
    assert match_eng is not None, f"TM miss for TIR->ENG: '{src_tir}'"
    print(f"Birth Cert [TIR->ENG]: '{match_eng.target_text}' (score={match_eng.score:.2f})")
    assert "birth certificate" in match_eng.target_text.lower()

    # Turn 11: Official seal and agreement letter (AMH -> SOM)
    src_amh = "እባክዎን በዚህ የውል ስምምነት ደብዳቤ ላይ የቀበሌውን ማህተም እና ፊርማ ያድርጉልኝ?"
    match_som = tm.lookup(src_amh, src_lang="amh", tgt_lang="som")
    assert match_som is not None, f"TM miss for AMH->SOM: '{src_amh}'"
    print(f"Official Seal [AMH->SOM]: '{match_som.target_text}' (score={match_som.score:.2f})")
    assert "shaabadda" in match_som.target_text.lower()

    print("✓ Kebele TM dialogue hits PASSED!")


def test_kebele_quick_replies():
    print("\n--- 4. Testing Kebele Quick Replies in All 5 Languages ---")
    langs = ["amh", "orm", "tir", "som", "eng"]
    for l in langs:
        replies = SmartSuggestionsEngine.get_suggestions(IntentType.CIVIC_GOV, l)
        assert len(replies) >= 3, f"Not enough suggestions for {l}"
        print(f"Quick replies for [{l}]: {len(replies)} suggestions")
        for r in replies:
            assert "text" in r and "translation" in r
    print("✓ Kebele Quick Replies in all 5 languages PASSED!")


if __name__ == "__main__":
    print("=" * 50)
    print("TESTING SCENARIO 5: KEBELE / CIVIC ADMINISTRATION")
    print("=" * 50)
    test_kebele_intent()
    test_kebele_idioms()
    test_kebele_tm_hits()
    test_kebele_quick_replies()
    print("\n" + "=" * 50)
    print("SCENARIO 5 (KEBELE / CIVIC) VERIFIED 100% SUCCESSFULLY!")
    print("=" * 50)
