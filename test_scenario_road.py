"""
Automated Verification Suite for Scenario 2: On a Road (Transit & Directions).

Validates:
1. Multi-lingual intent recognition (orm, amh, tir, som, eng) -> navigation_directions
2. Cultural road & transit safety idioms
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


def test_road_intent():
    print("\n--- 1. Testing Road Intent Classification ---")
    test_cases = [
        ("orm", "Buufata konkolaataa inni guddaan eessatti argama?", IntentType.DIRECTIONS),
        ("amh", "ባጃጅ ይዘህ በትልቁ አደባባይ ወደ ቀኝ ታጠፍ", IntentType.DIRECTIONS),
        ("tir", "ናብ ማእከል ከተማ ናይ ባጃጅ ታሪፍ ክንዲ ምንታይ እዩ", IntentType.DIRECTIONS),
        ("som", "Fadlan igu deji laydhka taraafikada ee soo socda agtiisa", IntentType.DIRECTIONS),
        ("eng", "Where is the nearest gas station to refill fuel?", IntentType.DIRECTIONS),
    ]

    for lang, text, expected in test_cases:
        intent = IntentClassifier.classify(text)
        print(f"[{lang.upper()}] '{text}' => Intent: {intent.value}")
        assert intent == expected, f"Expected {expected}, got {intent} for '{text}' ({lang})"
    print("✓ Road intent classification in all 5 languages PASSED!")


def test_road_idioms():
    print("\n--- 2. Testing Road Safety & Travel Idioms ---")
    # Amharic -> English
    eng_res = CulturalIdiomEngine.match_cultural_idiom("መንገዱን ያቅናልህ", src_lang="amh", tgt_lang="eng")
    print(f"Idiom [amh->eng] 'መንገዱን ያቅናልህ' => '{eng_res}'")
    assert eng_res is not None and "safe" in eng_res.lower()

    # Oromo -> Amharic
    amh_from_orm = CulturalIdiomEngine.match_cultural_idiom("nagaan deemi", src_lang="orm", tgt_lang="amh")
    print(f"Idiom [orm->amh] 'nagaan deemi' => '{amh_from_orm}'")
    assert amh_from_orm is not None and "መንገዱን" in amh_from_orm

    # Tigrinya -> Amharic
    amh_from_tir = CulturalIdiomEngine.match_cultural_idiom("ደሓን ኪድ", src_lang="tir", tgt_lang="amh")
    print(f"Idiom [tir->amh] 'ደሓን ኪድ' => '{amh_from_tir}'")
    assert amh_from_tir is not None and "በሰላም" in amh_from_tir

    # Somali -> Amharic
    amh_from_som = CulturalIdiomEngine.match_cultural_idiom("safaro wanaagsan", src_lang="som", tgt_lang="amh")
    print(f"Idiom [som->amh] 'safaro wanaagsan' => '{amh_from_som}'")
    assert amh_from_som is not None and "መልካም" in amh_from_som

    print("✓ Road safety and travel idioms PASSED!")


def test_road_tm_hits():
    print("\n--- 3. Testing Road TM Dialogue Hits ---")
    tm = TranslationMemory.get_instance()

    # Turn 5: Drop off at traffic light (ORM -> TIR)
    src_orm = "Maaloo ibsaa tiraafikii isa fuulduraa biratti na buusi."
    match_tir = tm.lookup(src_orm, src_lang="orm", tgt_lang="tir")
    assert match_tir is not None, f"TM miss for ORM->TIR: '{src_orm}'"
    print(f"Drop-off [ORM->TIR]: '{match_tir.target_text}' (score={match_tir.score:.2f})")
    assert "ትራፊክ" in match_tir.target_text

    # Turn 7: Handing 50 Birr and asking for change (SOM -> AMH)
    src_som = "Waa kan konton Birr, fadlan soo celi baaqiga."
    match_amh = tm.lookup(src_som, src_lang="som", tgt_lang="amh")
    assert match_amh is not None, f"TM miss for SOM->AMH: '{src_som}'"
    print(f"Change [SOM->AMH]: '{match_amh.target_text}' (score={match_amh.score:.2f})")
    assert "ሀምሳ ብር" in match_amh.target_text

    # Turn 11: Directions past the bridge (TIR -> ENG)
    src_tir = "ነቲ ድልድል ተሳጊርካ ነቲ መዕደሊ ነዳዲ ብሸነኽ ጸጋምካ ክትረኽቦ ኢኻ።"
    match_eng = tm.lookup(src_tir, src_lang="tir", tgt_lang="eng")
    assert match_eng is not None, f"TM miss for TIR->ENG: '{src_tir}'"
    print(f"Bridge [TIR->ENG]: '{match_eng.target_text}' (score={match_eng.score:.2f})")
    assert "bridge" in match_eng.target_text.lower()

    # Turn 2: Take bajaj at roundabout (ENG -> ORM)
    src_eng = "Take a bajaj and turn right at the big roundabout."
    match_orm = tm.lookup(src_eng, src_lang="eng", tgt_lang="orm")
    assert match_orm is not None, f"TM miss for ENG->ORM: '{src_eng}'"
    print(f"Roundabout [ENG->ORM]: '{match_orm.target_text}' (score={match_orm.score:.2f})")
    assert "baajaajii" in match_orm.target_text.lower()

    print("✓ Road TM dialogue hits PASSED!")


def test_road_quick_replies():
    print("\n--- 4. Testing Road Quick Replies in All 5 Languages ---")
    langs = ["amh", "orm", "tir", "som", "eng"]
    for l in langs:
        replies = SmartSuggestionsEngine.get_suggestions(IntentType.DIRECTIONS, l)
        assert len(replies) >= 3, f"Not enough suggestions for {l}"
        print(f"Quick replies for [{l}]: {len(replies)} suggestions")
        for r in replies:
            assert "text" in r and "translation" in r
    print("✓ Road Quick Replies in all 5 languages PASSED!")


if __name__ == "__main__":
    print("=" * 50)
    print("TESTING SCENARIO 2: ON A ROAD (TRANSIT & DIRECTIONS)")
    print("=" * 50)
    test_road_intent()
    test_road_idioms()
    test_road_tm_hits()
    test_road_quick_replies()
    print("\n" + "=" * 50)
    print("SCENARIO 2 (ON A ROAD) VERIFIED 100% SUCCESSFULLY!")
    print("=" * 50)
