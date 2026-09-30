"""
Automated Verification Suite for Scenario 8: Police Station & Legal Dispute Resolution.

Validates:
1. Multi-lingual intent recognition (orm, amh, tir, som, eng) -> legal_police
2. Cultural legal idioms (እውነትና ፍትህ ያሸንፋል, dhugaa fi haqi ni injifata, ሓቅን ፍትሕን ይስዕር, runta iyo caddaaladdu way guulaysan doontaa, ዳኝነት ይቅናህ)
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


def test_police_intent():
    print("\n--- 1. Testing Police & Legal Intent Classification ---")
    test_cases = [
        ("orm", "Akkam jirtu, sa'aatii muraasa dura manni koo waan hatameef iyyannoo yakkaa galmeessuun barbaada.", IntentType.LEGAL_POLICE),
        ("amh", "የዕለቱን የወንጀል መርማሪ ፖሊስ ጠርቼ ቃልዎን በዝርዝር እንዲመዘግብ አደርጋለሁ።", IntentType.LEGAL_POLICE),
        ("tir", "ፓስፖርት ንምእጋድን ንባንክ ንምሕባርን ናይ ፖሊስ መርትዖ ደብዳበ ክትህቡኒ ትኽእሉዶ?", IntentType.LEGAL_POLICE),
        ("som", "Waxaan u yeerayaa sarkaalka baareha dambiyada ee maanta jooga si uu qoraal rasmi ah kaaga qaado.", IntentType.LEGAL_POLICE),
        ("eng", "Can we also resolve a land boundary dispute with my neighbor through peaceful mediation and reconciliation?", IntentType.LEGAL_POLICE),
    ]

    for lang, text, expected in test_cases:
        intent = IntentClassifier.classify(text)
        print(f"[{lang.upper()}] '{text}' => Intent: {intent.value}")
        assert intent == expected, f"Expected {expected}, got {intent} for '{text}' ({lang})"
    print("✓ Police & Legal intent classification in all 5 languages PASSED!")


def test_police_idioms():
    print("\n--- 2. Testing Legal & Justice Idioms ---")
    # Amharic -> English: እውነትና ፍትህ ያሸንፋል
    eng_res = CulturalIdiomEngine.match_cultural_idiom("እውነትና ፍትህ ያሸንፋል", src_lang="amh", tgt_lang="eng")
    print(f"Idiom [amh->eng] 'እውነትና ፍትህ ያሸንፋል' => '{eng_res}'")
    assert eng_res is not None and "justice" in eng_res.lower()

    # Oromo -> Amharic: dhugaa fi haqi ni injifata
    amh_from_orm = CulturalIdiomEngine.match_cultural_idiom("dhugaa fi haqi ni injifata", src_lang="orm", tgt_lang="amh")
    print(f"Idiom [orm->amh] 'dhugaa fi haqi ni injifata' => '{amh_from_orm}'")
    assert amh_from_orm is not None and "እውነት" in amh_from_orm

    # Tigrinya -> Amharic: ሓቅን ፍትሕን ይስዕር
    amh_from_tir = CulturalIdiomEngine.match_cultural_idiom("ሓቅን ፍትሕን ይስዕር", src_lang="tir", tgt_lang="amh")
    print(f"Idiom [tir->amh] 'ሓቅን ፍትሕን ይስዕር' => '{amh_from_tir}'")
    assert amh_from_tir is not None and "እውነት" in amh_from_tir

    # Somali -> Amharic: runta iyo caddaaladdu way guulaysan doontaa
    amh_from_som = CulturalIdiomEngine.match_cultural_idiom("runta iyo caddaaladdu way guulaysan doontaa", src_lang="som", tgt_lang="amh")
    print(f"Idiom [som->amh] 'runta iyo caddaaladdu way guulaysan doontaa' => '{amh_from_som}'")
    assert amh_from_som is not None and "እውነት" in amh_from_som

    # Amharic -> Tigrinya: እውነትና ፍትህ ያሸንፋል
    tir_from_amh = CulturalIdiomEngine.match_cultural_idiom("እውነትና ፍትህ ያሸንፋል", src_lang="amh", tgt_lang="tir")
    print(f"Idiom [amh->tir] 'እውነትና ፍትህ ያሸንፋል' => '{tir_from_amh}'")
    assert tir_from_amh is not None and "ሓቅን" in tir_from_amh

    print("✓ Legal & Justice idioms PASSED!")


def test_police_tm_hits():
    print("\n--- 3. Testing Police TM Dialogue Hits ---")
    tm = TranslationMemory.get_instance()

    # Turn 1: Burglary & Crime Report (SOM -> AMH)
    src_som = "Nabadeey, dhowr saacadood ka hor gurigayga ayaa la jabsaday oo la xaday, waxaana rabaa inaan diiwaangeliyo cabasho dambiyeed."
    match_amh = tm.lookup(src_som, src_lang="som", tgt_lang="amh")
    assert match_amh is not None, f"TM miss for SOM->AMH: '{src_som}'"
    print(f"Burglary [SOM->AMH]: '{match_amh.target_text}' (score={match_amh.score:.2f})")
    assert "ወንጀል" in match_amh.target_text

    # Turn 3: Stolen laptop, cash and passports (ORM -> TIR)
    src_orm = "Laaptooppiin hojii, bilbilli harkaa, birrii kuma afurtamaa fi paaspoortiin maatii koo hatameera."
    match_tir = tm.lookup(src_orm, src_lang="orm", tgt_lang="tir")
    assert match_tir is not None, f"TM miss for ORM->TIR: '{src_orm}'"
    print(f"Stolen Items [ORM->TIR]: '{match_tir.target_text}' (score={match_tir.score:.2f})")
    assert "ተሰሪቖም" in match_tir.target_text

    # Turn 7: Forensics dusting for fingerprints (ENG -> ORM)
    src_eng = "We will open an investigation file, secure the video evidence, and dispatch a forensics unit to dust for fingerprints."
    match_orm = tm.lookup(src_eng, src_lang="eng", tgt_lang="orm")
    assert match_orm is not None, f"TM miss for ENG->ORM: '{src_eng}'"
    print(f"Forensics [ENG->ORM]: '{match_orm.target_text}' (score={match_orm.score:.2f})")
    assert "ashaaraa" in match_orm.target_text.lower()

    # Turn 8: Signing witness statement (TIR -> ENG)
    src_tir = "እቲ ዝሃብክምዎ ቃል ኣንቢብኩም ኣረጋግጹ፣ ኣብ መወዳእታ ምሉእ ስምኩም ጽሒፍኩም ፈርሙ።"
    match_eng = tm.lookup(src_tir, src_lang="tir", tgt_lang="eng")
    assert match_eng is not None, f"TM miss for TIR->ENG: '{src_tir}'"
    print(f"Sign Statement [TIR->ENG]: '{match_eng.target_text}' (score={match_eng.score:.2f})")
    assert "statement" in match_eng.target_text.lower()

    # Turn 14: Case file number and truth will prevail (AMH -> SOM)
    src_amh = "የመዝገብ ቁጥርዎ ይኸውልዎት፣ የምርመራ ቡድኑ ሌባውን ይከታተላል፣ እውነትና ፍትህ ያሸንፋል!"
    match_som = tm.lookup(src_amh, src_lang="amh", tgt_lang="som")
    assert match_som is not None, f"TM miss for AMH->SOM: '{src_amh}'"
    print(f"Case File [AMH->SOM]: '{match_som.target_text}' (score={match_som.score:.2f})")
    assert "caddaaladdu" in match_som.target_text.lower()

    print("✓ Police TM dialogue hits PASSED!")


def test_police_quick_replies():
    print("\n--- 4. Testing Police Quick Replies in All 5 Languages ---")
    langs = ["amh", "orm", "tir", "som", "eng"]
    for l in langs:
        replies = SmartSuggestionsEngine.get_suggestions(IntentType.LEGAL_POLICE, l)
        assert len(replies) >= 3, f"Not enough suggestions for {l}"
        print(f"Quick replies for [{l}]: {len(replies)} suggestions")
        for r in replies:
            assert "text" in r and "translation" in r
    print("✓ Police Quick Replies in all 5 languages PASSED!")


if __name__ == "__main__":
    print("=" * 50)
    print("TESTING SCENARIO 8: POLICE STATION & LEGAL DISPUTE RESOLUTION")
    print("=" * 50)
    test_police_intent()
    test_police_idioms()
    test_police_tm_hits()
    test_police_quick_replies()
    print("\n" + "=" * 50)
    print("SCENARIO 8 (POLICE & LEGAL) VERIFIED 100% SUCCESSFULLY!")
    print("=" * 50)
