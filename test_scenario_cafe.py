"""
Automated Verification Suite for Scenario 3: In a Cafe (Buna Culture & Hospitality).

Validates:
1. Multi-lingual intent recognition (orm, amh, tir, som, eng) -> dining_hospitality
2. Cultural cafe & buna idioms (e.g., ቡና ጠጡ, buna dhugaa, ቡን ስተዩ, bun cabba, እጅህ ይባረክ)
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


def test_cafe_intent():
    print("\n--- 1. Testing Cafe Intent Classification ---")
    test_cases = [
        ("orm", "Buna jabanaa haaraa xenaa addaamaa qabu nuuf danfisi", IntentType.DINING),
        ("amh", "በጤና አዳም የተፈላ ትኩስ የጀበና ቡና ልታፈላልን ትችላለህ?", IntentType.DINING),
        ("tir", "ናይ ኣቦል ዙር ቡን ኣብ ውሽጢ ሓሙሽተ ደቒቕ ክቐርብ እዩ", IntentType.DINING),
        ("som", "Fadlan maakiyaatada iyo shaaha nooga dhig kuwo aan sonkor lahayn", IntentType.DINING),
        ("eng", "Can you brew a fresh clay pot of Jebena coffee with rue herb for us?", IntentType.DINING),
    ]

    for lang, text, expected in test_cases:
        intent = IntentClassifier.classify(text)
        print(f"[{lang.upper()}] '{text}' => Intent: {intent.value}")
        assert intent == expected, f"Expected {expected}, got {intent} for '{text}' ({lang})"
    print("✓ Cafe intent classification in all 5 languages PASSED!")


def test_cafe_idioms():
    print("\n--- 2. Testing Cafe & Buna Culture Idioms ---")
    # Amharic -> English
    eng_res = CulturalIdiomEngine.match_cultural_idiom("ቡና ጠጡ", src_lang="amh", tgt_lang="eng")
    print(f"Idiom [amh->eng] 'ቡና ጠጡ' => '{eng_res}'")
    assert eng_res is not None and "coffee" in eng_res.lower()

    # Oromo -> Amharic
    amh_from_orm = CulturalIdiomEngine.match_cultural_idiom("buna dhugaa", src_lang="orm", tgt_lang="amh")
    print(f"Idiom [orm->amh] 'buna dhugaa' => '{amh_from_orm}'")
    assert amh_from_orm is not None and "ቡና" in amh_from_orm

    # Tigrinya -> Amharic
    amh_from_tir = CulturalIdiomEngine.match_cultural_idiom("ቡን ስተዩ", src_lang="tir", tgt_lang="amh")
    print(f"Idiom [tir->amh] 'ቡን ስተዩ' => '{amh_from_tir}'")
    assert amh_from_tir is not None and "ቡና" in amh_from_tir

    # Somali -> Amharic
    amh_from_som = CulturalIdiomEngine.match_cultural_idiom("bun cabba", src_lang="som", tgt_lang="amh")
    print(f"Idiom [som->amh] 'bun cabba' => '{amh_from_som}'")
    assert amh_from_som is not None and "ቡና" in amh_from_som

    # Blessing hands: Amharic -> English
    bless_eng = CulturalIdiomEngine.match_cultural_idiom("እጅህ ይባረክ", src_lang="amh", tgt_lang="eng")
    print(f"Idiom [amh->eng] 'እጅህ ይባረክ' => '{bless_eng}'")
    assert bless_eng is not None and "hands" in bless_eng.lower()

    print("✓ Cafe and Buna culture idioms PASSED!")


def test_cafe_tm_hits():
    print("\n--- 3. Testing Cafe TM Dialogue Hits ---")
    tm = TranslationMemory.get_instance()

    # Turn 3: Brew Jebena coffee with rue (ORM -> TIR)
    src_orm = "Buna jabanaa haaraa xenaa addaamaa qabu nuuf danfisuu dandeessaa?"
    match_tir = tm.lookup(src_orm, src_lang="orm", tgt_lang="tir")
    assert match_tir is not None, f"TM miss for ORM->TIR: '{src_orm}'"
    print(f"Jebena Brew [ORM->TIR]: '{match_tir.target_text}' (score={match_tir.score:.2f})")
    assert "ጀበና" in match_tir.target_text

    # Turn 10: Fasting lentil sambusa (SOM -> AMH)
    src_som = "Haa, waxaan haynaa sambuus diirran oo misir ah iyo keeg qudaar ah."
    match_amh = tm.lookup(src_som, src_lang="som", tgt_lang="amh")
    assert match_amh is not None, f"TM miss for SOM->AMH: '{src_som}'"
    print(f"Fasting Snacks [SOM->AMH]: '{match_amh.target_text}' (score={match_amh.score:.2f})")
    assert "ሳምቡሳ" in match_amh.target_text

    # Turn 8: Sugar-free macchiato and tea (TIR -> ENG)
    src_tir = "በጃኻ ነቲ ማክያቶን ሻህን ጭራሽ ብዘይ ሽኮር ግበረልና።"
    match_eng = tm.lookup(src_tir, src_lang="tir", tgt_lang="eng")
    assert match_eng is not None, f"TM miss for TIR->ENG: '{src_tir}'"
    print(f"Sugar-free [TIR->ENG]: '{match_eng.target_text}' (score={match_eng.score:.2f})")
    assert "macchiato" in match_eng.target_text.lower()

    # Turn 4: First round Abol coffee (ENG -> ORM)
    src_eng = "Certainly, the first round Abol coffee will be served in five minutes."
    match_orm = tm.lookup(src_eng, src_lang="eng", tgt_lang="orm")
    assert match_orm is not None, f"TM miss for ENG->ORM: '{src_eng}'"
    print(f"Abol Round [ENG->ORM]: '{match_orm.target_text}' (score={match_orm.score:.2f})")
    assert "aboliin" in match_orm.target_text.lower()

    # Turn 13: Customer requesting bill (AMH -> SOM)
    src_amh = "አስተናጋጅ፣ እባክህ ሒሳባችንን አስልተህ ልታመጣልን ትችላለህ?"
    match_som = tm.lookup(src_amh, src_lang="amh", tgt_lang="som")
    assert match_som is not None, f"TM miss for AMH->SOM: '{src_amh}'"
    print(f"Bill [AMH->SOM]: '{match_som.target_text}' (score={match_som.score:.2f})")
    assert "biilka" in match_som.target_text.lower()

    print("✓ Cafe TM dialogue hits PASSED!")


def test_cafe_quick_replies():
    print("\n--- 4. Testing Cafe Quick Replies in All 5 Languages ---")
    langs = ["amh", "orm", "tir", "som", "eng"]
    for l in langs:
        replies = SmartSuggestionsEngine.get_suggestions(IntentType.DINING, l)
        assert len(replies) >= 3, f"Not enough suggestions for {l}"
        print(f"Quick replies for [{l}]: {len(replies)} suggestions")
        for r in replies:
            assert "text" in r and "translation" in r
    print("✓ Cafe Quick Replies in all 5 languages PASSED!")


if __name__ == "__main__":
    print("=" * 50)
    print("TESTING SCENARIO 3: IN A CAFE (BUNA CULTURE & FOOD)")
    print("=" * 50)
    test_cafe_intent()
    test_cafe_idioms()
    test_cafe_tm_hits()
    test_cafe_quick_replies()
    print("\n" + "=" * 50)
    print("SCENARIO 3 (IN A CAFE) VERIFIED 100% SUCCESSFULLY!")
    print("=" * 50)
