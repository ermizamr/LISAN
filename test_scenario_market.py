"""
Automated Verification Suite for Scenario 4: In a Market (Trade, Bargaining & Produce).

Validates:
1. Multi-lingual intent recognition (orm, amh, tir, som, eng) -> commerce_bargaining
2. Cultural market idioms (ይቁረጡት, gatii dhumaa natti himi, ቁረጸለይ, qiimaha ugu dambeeya ii sheeg, በረከቱ ይግባህ, ገበያ ይቅናልህ)
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


def test_market_intent():
    print("\n--- 1. Testing Market Intent Classification ---")
    test_cases = [
        ("orm", "Gatii dhumaa birrii kuma jahaa fi dhibba shan siif godha", IntentType.BARGAINING),
        ("amh", "ቀይ ሽንኩርት እና ነጭ ሽንኩርት በኪሎ ስንት ስንት ናቸው?", IntentType.BARGAINING),
        ("tir", "ናይ ቀዳማይ ብርኪ ጻዕዳ ጣፍ ኩንታል ክንዲ ምንታይ እዩ?", IntentType.BARGAINING),
        ("som", "Waa imisa qiimaha kiintaalka teff-ka cad ee tayada koowaad?", IntentType.BARGAINING),
        ("eng", "How much is a quintal of this Grade One white teff?", IntentType.BARGAINING),
    ]

    for lang, text, expected in test_cases:
        intent = IntentClassifier.classify(text)
        print(f"[{lang.upper()}] '{text}' => Intent: {intent.value}")
        assert intent == expected, f"Expected {expected}, got {intent} for '{text}' ({lang})"
    print("✓ Market intent classification in all 5 languages PASSED!")


def test_market_idioms():
    print("\n--- 2. Testing Market & Bargaining Idioms ---")
    # Amharic -> English: ይቁረጡት
    eng_res = CulturalIdiomEngine.match_cultural_idiom("ይቁረጡት", src_lang="amh", tgt_lang="eng")
    print(f"Idiom [amh->eng] 'ይቁረጡት' => '{eng_res}'")
    assert eng_res is not None and "final" in eng_res.lower()

    # Oromo -> Amharic: gatii dhumaa natti himi
    amh_from_orm = CulturalIdiomEngine.match_cultural_idiom("gatii dhumaa natti himi", src_lang="orm", tgt_lang="amh")
    print(f"Idiom [orm->amh] 'gatii dhumaa natti himi' => '{amh_from_orm}'")
    assert amh_from_orm is not None and "ዋጋ" in amh_from_orm

    # Tigrinya -> Amharic: ቁረጸለይ
    amh_from_tir = CulturalIdiomEngine.match_cultural_idiom("ቁረጸለይ", src_lang="tir", tgt_lang="amh")
    print(f"Idiom [tir->amh] 'ቁረጸለይ' => '{amh_from_tir}'")
    assert amh_from_tir is not None and "ይቁረጡት" in amh_from_tir

    # Somali -> Amharic: qiimaha ugu dambeeya ii sheeg
    amh_from_som = CulturalIdiomEngine.match_cultural_idiom("qiimaha ugu dambeeya ii sheeg", src_lang="som", tgt_lang="amh")
    print(f"Idiom [som->amh] 'qiimaha ugu dambeeya ii sheeg' => '{amh_from_som}'")
    assert amh_from_som is not None and "ዋጋ" in amh_from_som

    # Merchant blessing: Amharic -> Tigrinya: በረከቱ ይግባህ
    tir_from_amh = CulturalIdiomEngine.match_cultural_idiom("በረከቱ ይግባህ", src_lang="amh", tgt_lang="tir")
    print(f"Idiom [amh->tir] 'በረከቱ ይግባህ' => '{tir_from_amh}'")
    assert tir_from_amh is not None and ("blessed" in tir_from_amh.lower() or "በረኸት" in tir_from_amh)

    print("✓ Market and bargaining idioms PASSED!")


def test_market_tm_hits():
    print("\n--- 3. Testing Market TM Dialogue Hits ---")
    tm = TranslationMemory.get_instance()

    # Turn 1: White teff quintal price (ORM -> TIR)
    src_orm = "Akkam jirtu, xaafiin adii sadarkaa tokkoffaa kun kuntaalli meeqa?"
    match_tir = tm.lookup(src_orm, src_lang="orm", tgt_lang="tir")
    assert match_tir is not None, f"TM miss for ORM->TIR: '{src_orm}'"
    print(f"Teff Price [ORM->TIR]: '{match_tir.target_text}' (score={match_tir.score:.2f})")
    assert "ጣፍ" in match_tir.target_text

    # Turn 5: Price of onions and garlic (SOM -> AMH)
    src_som = "Waa immisa basasha gaduudan iyo toonta kiiloodiiba?"
    match_amh = tm.lookup(src_som, src_lang="som", tgt_lang="amh")
    assert match_amh is not None, f"TM miss for SOM->AMH: '{src_som}'"
    print(f"Produce [SOM->AMH]: '{match_amh.target_text}' (score={match_amh.score:.2f})")
    assert "ሽንኩርት" in match_amh.target_text

    # Turn 7: Weighing on scale (TIR -> ENG)
    src_tir = "በጃኻ ኣብቲ ሚዛን ሰለስተ ኪሎ ሽጉርትን ክልተ ኪሎ ውዑይ ቲማቲምን ሚዚንካ ሃበኒ።"
    match_eng = tm.lookup(src_tir, src_lang="tir", tgt_lang="eng")
    assert match_eng is not None, f"TM miss for TIR->ENG: '{src_tir}'"
    print(f"Scale Weigh [TIR->ENG]: '{match_eng.target_text}' (score={match_eng.score:.2f})")
    assert "weigh" in match_eng.target_text.lower()

    # Turn 10: 20 spices blended into berbere (ENG -> ORM)
    src_eng = "Yes, this berbere has all twenty sacred spices blended into it."
    match_orm = tm.lookup(src_eng, src_lang="eng", tgt_lang="orm")
    assert match_orm is not None, f"TM miss for ENG->ORM: '{src_eng}'"
    print(f"Spices [ENG->ORM]: '{match_orm.target_text}' (score={match_orm.score:.2f})")
    assert "barbarreen" in match_orm.target_text.lower()

    # Turn 13: Cash and receipt (AMH -> SOM)
    src_amh = "ሰባት ሺህ ብር ጥሬ ገንዘብ ይኸውልህ፣ እባክህ መልሴንና ደረሰኝ ስጠኝ።"
    match_som = tm.lookup(src_amh, src_lang="amh", tgt_lang="som")
    assert match_som is not None, f"TM miss for AMH->SOM: '{src_amh}'"
    print(f"Receipt [AMH->SOM]: '{match_som.target_text}' (score={match_som.score:.2f})")
    assert "rasiidka" in match_som.target_text.lower()

    print("✓ Market TM dialogue hits PASSED!")


def test_market_quick_replies():
    print("\n--- 4. Testing Market Quick Replies in All 5 Languages ---")
    langs = ["amh", "orm", "tir", "som", "eng"]
    for l in langs:
        replies = SmartSuggestionsEngine.get_suggestions(IntentType.BARGAINING, l)
        assert len(replies) >= 3, f"Not enough suggestions for {l}"
        print(f"Quick replies for [{l}]: {len(replies)} suggestions")
        for r in replies:
            assert "text" in r and "translation" in r
    print("✓ Market Quick Replies in all 5 languages PASSED!")


if __name__ == "__main__":
    print("=" * 50)
    print("TESTING SCENARIO 4: IN A MARKET (TRADE & BARGAINING)")
    print("=" * 50)
    test_market_intent()
    test_market_idioms()
    test_market_tm_hits()
    test_market_quick_replies()
    print("\n" + "=" * 50)
    print("SCENARIO 4 (IN A MARKET) VERIFIED 100% SUCCESSFULLY!")
    print("=" * 50)
