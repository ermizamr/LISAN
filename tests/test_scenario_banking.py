"""
Automated Verification Suite for Scenario 6: Commercial Banking & Mobile Money.

Validates:
1. Multi-lingual intent recognition (orm, amh, tir, som, eng) -> commercial_banking
2. Cultural banking idioms (ገንዘብህ ይባረክ, maallaqni kee haa eebbifamu, ገንዘብካ ይባረኽ, lacagtaadu ha barakoowdo, በረከት ይኑረው)
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


def test_banking_intent():
    print("\n--- 1. Testing Banking Intent Classification ---")
    test_cases = [
        ("orm", "Akkam jirtu, herrega qusannaa koo keessatti maallaqa callaa galchuu nan barbaada.", IntentType.BANKING),
        ("amh", "ትናንት ማታ የኤቲኤም ካርዴ እዚህ ባንክ ማሽን ላይ ተውጦብኛል።", IntentType.BANKING),
        ("tir", "ነዚ ናይ ባንክ ሕሳበይ ምስ ሞባይል ባንኪንግን ቴሌብርን ከተሓሕዞ እኽእልዶ?", IntentType.BANKING),
        ("som", "Waxaa iiga yimid qoyskayga xawaalad doolarka Maraykanka ah, waxaan rabaa inaan ku qaato sarrifka rasmiga ah ee bangiga.", IntentType.BANKING),
        ("eng", "How much can I transfer to another bank per day, and what is the transaction fee?", IntentType.BANKING),
    ]

    for lang, text, expected in test_cases:
        intent = IntentClassifier.classify(text)
        print(f"[{lang.upper()}] '{text}' => Intent: {intent.value}")
        assert intent == expected, f"Expected {expected}, got {intent} for '{text}' ({lang})"
    print("✓ Banking intent classification in all 5 languages PASSED!")


def test_banking_idioms():
    print("\n--- 2. Testing Banking & Wealth Idioms ---")
    # Amharic -> English: ገንዘብህ ይባረክ
    eng_res = CulturalIdiomEngine.match_cultural_idiom("ገንዘብህ ይባረክ", src_lang="amh", tgt_lang="eng")
    print(f"Idiom [amh->eng] 'ገንዘብህ ይባረክ' => '{eng_res}'")
    assert eng_res is not None and "wealth" in eng_res.lower()

    # Oromo -> Amharic: maallaqni kee haa eebbifamu
    amh_from_orm = CulturalIdiomEngine.match_cultural_idiom("maallaqni kee haa eebbifamu", src_lang="orm", tgt_lang="amh")
    print(f"Idiom [orm->amh] 'maallaqni kee haa eebbifamu' => '{amh_from_orm}'")
    assert amh_from_orm is not None and "ገንዘብህ" in amh_from_orm

    # Tigrinya -> Amharic: ገንዘብካ ይባረኽ
    amh_from_tir = CulturalIdiomEngine.match_cultural_idiom("ገንዘብካ ይባረኽ", src_lang="tir", tgt_lang="amh")
    print(f"Idiom [tir->amh] 'ገንዘብካ ይባረኽ' => '{amh_from_tir}'")
    assert amh_from_tir is not None and "ገንዘብህ" in amh_from_tir

    # Somali -> Amharic: lacagtaadu ha barakoowdo
    amh_from_som = CulturalIdiomEngine.match_cultural_idiom("lacagtaadu ha barakoowdo", src_lang="som", tgt_lang="amh")
    print(f"Idiom [som->amh] 'lacagtaadu ha barakoowdo' => '{amh_from_som}'")
    assert amh_from_som is not None and "ገንዘብህ" in amh_from_som

    # Amharic -> Tigrinya: ገንዘብህ ይባረክ
    tir_from_amh = CulturalIdiomEngine.match_cultural_idiom("ገንዘብህ ይባረክ", src_lang="amh", tgt_lang="tir")
    print(f"Idiom [amh->tir] 'ገንዘብህ ይባረክ' => '{tir_from_amh}'")
    assert tir_from_amh is not None and "ገንዘብካ" in tir_from_amh

    print("✓ Banking & Wealth idioms PASSED!")


def test_banking_tm_hits():
    print("\n--- 3. Testing Banking TM Dialogue Hits ---")
    tm = TranslationMemory.get_instance()

    # Turn 2: Passbook & ID request (SOM -> AMH)
    src_som = "Fadlan i sii kaarkaaga aqoonsiga iyo buugga bangiga oo uu ku qoran yahay lambarka akoonku."
    match_amh = tm.lookup(src_som, src_lang="som", tgt_lang="amh")
    assert match_amh is not None, f"TM miss for SOM->AMH: '{src_som}'"
    print(f"Passbook [SOM->AMH]: '{match_amh.target_text}' (score={match_amh.score:.2f})")
    assert "ደብተር" in match_amh.target_text

    # Turn 6: USSD and mobile app setup (ORM -> TIR)
    src_orm = "Eeyyee, foomii tajaajila dijitaalaa mallatteessuudhaan koodii USSD fi appii bilbilaa fayyadamuu dandeessu."
    match_tir = tm.lookup(src_orm, src_lang="orm", tgt_lang="tir")
    assert match_tir is not None, f"TM miss for ORM->TIR: '{src_orm}'"
    print(f"Digital App [ORM->TIR]: '{match_tir.target_text}' (score={match_tir.score:.2f})")
    assert "USSD" in match_tir.target_text

    # Turn 9: Captured ATM card (ENG -> ORM)
    src_eng = "Yesterday evening my ATM card was captured by this branch's ATM machine."
    match_orm = tm.lookup(src_eng, src_lang="eng", tgt_lang="orm")
    assert match_orm is not None, f"TM miss for ENG->ORM: '{src_eng}'"
    print(f"ATM Captured [ENG->ORM]: '{match_orm.target_text}' (score={match_orm.score:.2f})")
    assert "eetiyeemii" in match_orm.target_text.lower()

    # Turn 11: Remittance US dollars exchange (TIR -> ENG)
    src_tir = "ካብ ስድራቤተይ ብናይ ኣመሪካ ዶላር እተላእከ ሓዋላ ኣሎኒ፣ ብሕጋዊ ናይ ባንክ ሸርፊ ከውጽኦ እደሊ ኣለኹ።"
    match_eng = tm.lookup(src_tir, src_lang="tir", tgt_lang="eng")
    assert match_eng is not None, f"TM miss for TIR->ENG: '{src_tir}'"
    print(f"Remittance [TIR->ENG]: '{match_eng.target_text}' (score={match_eng.score:.2f})")
    assert "remittance" in match_eng.target_text.lower()

    # Turn 8: EthSwitch transfer limit (AMH -> SOM)
    src_amh = "በኢትስዊች በኩል እስከ አንድ መቶ ሺህ ብር በትንሽ ክፍያ በጥቂት ደቂቃዎች ውስጥ ይተላለፋል።"
    match_som = tm.lookup(src_amh, src_lang="amh", tgt_lang="som")
    assert match_som is not None, f"TM miss for AMH->SOM: '{src_amh}'"
    print(f"EthSwitch [AMH->SOM]: '{match_som.target_text}' (score={match_som.score:.2f})")
    assert "ethswitch" in match_som.target_text.lower()

    print("✓ Banking TM dialogue hits PASSED!")


def test_banking_quick_replies():
    print("\n--- 4. Testing Banking Quick Replies in All 5 Languages ---")
    langs = ["amh", "orm", "tir", "som", "eng"]
    for l in langs:
        replies = SmartSuggestionsEngine.get_suggestions(IntentType.BANKING, l)
        assert len(replies) >= 3, f"Not enough suggestions for {l}"
        print(f"Quick replies for [{l}]: {len(replies)} suggestions")
        for r in replies:
            assert "text" in r and "translation" in r
    print("✓ Banking Quick Replies in all 5 languages PASSED!")


if __name__ == "__main__":
    print("=" * 50)
    print("TESTING SCENARIO 6: COMMERCIAL BANKING & MOBILE MONEY")
    print("=" * 50)
    test_banking_intent()
    test_banking_idioms()
    test_banking_tm_hits()
    test_banking_quick_replies()
    print("\n" + "=" * 50)
    print("SCENARIO 6 (BANKING) VERIFIED 100% SUCCESSFULLY!")
    print("=" * 50)
