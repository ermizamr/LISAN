"""
Complete Verification Suite for Hackathon Quad-Lingual Stabilization Solution.

Tests:
1. Entity Shield (Afaan Oromoo, Amharic, Tigrinya, Somali, English)
2. Hallucination & Degeneration Guard
3. Quad-Lingual High-Value Translation Memory Hits
4. SmartEngine Metadata & Confidence Integration
"""

import sys
from pathlib import Path

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_pipeline.entity_shield import EntityShield
from ai_pipeline.hallucination_guard import HallucinationGuard
from ai_pipeline.translation_memory import TranslationMemory
from ai_pipeline.smart_engine import SmartEngine


def test_entity_shield_oromo():
    print("\n--- Test 1: Afaan Oromoo Entity Shield ---")
    source = "xiinxalaan siyaasaa obbo jawaa mohammada dhimma kana ibsaniiru"
    shielded, entities = EntityShield.shield(source, "orm")
    print(f"Source: {source}")
    print(f"Shielded: {shielded}")
    assert len(entities) == 1, f"Expected 1 entity, got {len(entities)}"
    assert entities[0].title_category == "political_analyst_mr"
    
    # English target
    res_en = EntityShield.unshield(shielded, entities, "orm", "eng")
    print(f"Restored EN: {res_en}")
    assert "Political Analyst Mr." in res_en
    assert "Jawar Mohammed" in res_en

    # Amharic target
    res_am = EntityShield.unshield(shielded, entities, "orm", "amh")
    print(f"Restored AM: {res_am}")
    assert "የፖለቲካ ተንታኝ አቶ" in res_am
    assert "ጃዋር" in res_am

    # Tigrinya target
    res_ti = EntityShield.unshield(shielded, entities, "orm", "tir")
    print(f"Restored TI: {res_ti}")
    assert "ናይ ፖለቲካ ተንታኒ ኣቶ" in res_ti

    # Somali target
    res_so = EntityShield.unshield(shielded, entities, "orm", "som")
    print(f"Restored SO: {res_so}")
    assert "Falanqeeyaha Siyaasadda Mudane" in res_so
    print("✓ Oromo Entity Shield PASSED!")


def test_entity_shield_somali():
    print("\n--- Test 2: Somali Entity Shield ---")
    source = "Madaxweyne Xasan Sheekh ayaa ka hadlay xaaladda dalka"
    shielded, entities = EntityShield.shield(source, "som")
    print(f"Source: {source}")
    print(f"Shielded: {shielded}")
    assert len(entities) == 1
    assert entities[0].title_category == "president"

    # English target
    res_en = EntityShield.unshield(shielded, entities, "som", "eng")
    print(f"Restored EN: {res_en}")
    assert "President" in res_en

    # Amharic target
    res_am = EntityShield.unshield(shielded, entities, "som", "amh")
    print(f"Restored AM: {res_am}")
    assert "ፕሬዝዳንት" in res_am

    print("✓ Somali Entity Shield PASSED!")


def test_entity_shield_tigrinya():
    print("\n--- Test 3: Tigrinya Entity Shield ---")
    source = "ኣቶ ገብረመድህን ተዛሪቦም"
    shielded, entities = EntityShield.shield(source, "tir")
    print(f"Source: {source}")
    print(f"Shielded: {shielded}")
    assert len(entities) == 1
    assert entities[0].title_category == "mr"

    # English target
    res_en = EntityShield.unshield(shielded, entities, "tir", "eng")
    print(f"Restored EN: {res_en}")
    assert "Mr." in res_en
    assert "Gebremedhin" in res_en

    # Oromo target
    res_om = EntityShield.unshield(shielded, entities, "tir", "orm")
    print(f"Restored ORM: {res_om}")
    assert "Obbo" in res_om
    assert "Gebremedhin" in res_om

    print("✓ Tigrinya Entity Shield PASSED!")


def test_hallucination_guard():
    print("\n--- Test 4: Hallucination & Degeneration Guard ---")
    # Clean TM hit
    r_tm = HallucinationGuard.evaluate("Akkam jirtu", "እንደምን ናችሁ", "orm", "amh", is_tm_hit=True)
    assert r_tm.is_tm_hit is True
    assert r_tm.confidence >= 0.95
    assert r_tm.warning is None

    # Length anomaly (hallucination essay)
    r_long = HallucinationGuard.evaluate(
        "nagaa qabna galatoomaa",
        "market research is a comprehensive study of commercial products and financial indices across worldwide trading centers and agricultural markets in the eastern region",
        "orm", "eng"
    )
    print(f"Long translation check: conf={r_long.confidence}, warning={r_long.warning}")
    assert r_long.is_uncertain is True
    assert r_long.confidence <= 0.60
    assert "long" in r_long.warning.lower()

    # Repetition loop
    r_rep = HallucinationGuard.evaluate(
        "I need help",
        "help me help me help me help me help me",
        "eng", "eng"
    )
    print(f"Repetition check: conf={r_rep.confidence}, warning={r_rep.warning}")
    assert r_rep.is_uncertain is True

    print("✓ Hallucination Guard PASSED!")


def test_quad_lingual_tm():
    print("\n--- Test 5: Quad-Lingual TM Seeded Hits ---")
    tm = TranslationMemory.get_instance()
    
    # Healthcare: orm -> tir
    m1 = tm.lookup("Mee hospitaalli ykn kiliniikiin dhihoo eessa jira?", "orm", "tir")
    assert m1 is not None, "Failed to match healthcare orm->tir"
    assert "ሆስፒታል" in m1.target_text or "ክሊኒክ" in m1.target_text
    print(f"ORM->TIR Healthcare: '{m1.target_text}' (score={m1.score})")

    # Greetings: som -> amh
    m2 = tm.lookup("Sidee tihiin? Caafimaadkiinna sidee yahay?", "som", "amh")
    assert m2 is not None, "Failed to match greetings som->amh"
    assert "እንደምን" in m2.target_text
    print(f"SOM->AMH Greetings: '{m2.target_text}' (score={m2.score})")

    # Commerce: amh -> orm
    m3 = tm.lookup("የዚህ ዋጋ ስንት ነው? መቀነስ ትችላላችሁ?", "amh", "orm")
    assert m3 is not None, "Failed to match commerce amh->orm"
    assert "gatiin" in m3.target_text.lower()
    print(f"AMH->ORM Commerce: '{m3.target_text}' (score={m3.score})")

    print("✓ Quad-Lingual TM Hits PASSED!")


def test_smart_engine_integration():
    print("\n--- Test 6: SmartEngine Guard Integration ---")
    # Mock NMT translator function returning rich result
    def mock_translator(text, src, tgt):
        shielded, ents = EntityShield.shield(text, src)
        unshielded = EntityShield.unshield(shielded, ents, src, tgt)
        return {
            "translated_text": f"[Translated] {unshielded}",
            "confidence": 0.88,
            "is_tm_match": False,
            "entities_preserved": [e.name_part for e in ents],
            "warning": None,
        }

    res = SmartEngine.process_and_translate(
        text="xiinxalaan siyaasaa obbo jawaa mohammada dhimma kana ibsaniiru",
        src_lang="orm",
        tgt_lang="eng",
        nmt_translator_func=mock_translator,
    )
    print(f"SmartEngine output: {res.translated_text}")
    print(f"Confidence: {res.confidence}, TM Match: {res.is_tm_match}, Entities: {res.entities_preserved}")
    assert res.confidence == 0.88
    assert "Political Analyst Mr." in res.translated_text
    assert "Jawar Mohammed" in res.translated_text
    assert len(res.entities_preserved) >= 1

    print("✓ SmartEngine Integration PASSED!")


if __name__ == "__main__":
    print("==================================================")
    print("RUNNING HACKATHON SOLUTION COMPREHENSIVE SUITE")
    print("==================================================")
    test_entity_shield_oromo()
    test_entity_shield_somali()
    test_entity_shield_tigrinya()
    test_hallucination_guard()
    test_quad_lingual_tm()
    test_smart_engine_integration()
    print("\n==================================================")
    print("ALL 6 PHASES PASSED WITH 100% SUCCESS!")
    print("==================================================")
