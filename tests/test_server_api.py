"""
Verify FastAPI endpoints with the new Hackathon Guard fields.
"""

import sys
from pathlib import Path

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from server import app

class MockPipeline:
    def translate_text_smart(self, text, src, tgt, session_id=None, formality="auto"):
        from ai_pipeline.translation_memory import TranslationMemory
        tm_match = TranslationMemory.get_instance().lookup(text, src, tgt)
        if tm_match:
            return {
                "source_text": text,
                "translated_text": tm_match.target_text,
                "src_lang": src,
                "tgt_lang": tgt,
                "intent": "emergency_medical" if "hospital" in text.lower() or "hospitaal" in text.lower() else "greetings",
                "formality": formality,
                "suggested_replies": [],
                "confidence": 1.0,
                "is_tm_match": True,
                "entities_preserved": [],
                "warning": None,
            }
        return {
            "source_text": text,
            "translated_text": f"Translated {text}",
            "src_lang": src,
            "tgt_lang": tgt,
            "intent": "general_conversation",
            "formality": formality,
            "suggested_replies": [],
            "confidence": 0.85,
            "is_tm_match": False,
            "entities_preserved": [],
            "warning": None,
        }

app.state.pipeline = MockPipeline()
client = TestClient(app)

def test_endpoints():
    print("Testing GET /health...")
    r_health = client.get("/health")
    print("Health:", r_health.status_code, r_health.json())
    assert r_health.status_code == 200

    print("\nTesting POST /translate/text for verified TM match...")
    payload_tm = {
        "text": "Mee hospitaalli ykn kiliniikiin dhihoo eessa jira?",
        "src": "orm",
        "tgt": "tir",
    }
    r_tm = client.post("/translate/text", json=payload_tm)
    print("TM status:", r_tm.status_code)
    data_tm = r_tm.json()
    print("TM response:", data_tm)
    assert r_tm.status_code == 200
    assert data_tm["is_tm_match"] is True
    assert data_tm["confidence"] >= 0.95
    assert "ሆስፒታል" in data_tm["translated_text"] or "ክሊኒክ" in data_tm["translated_text"]

    print("\nTesting POST /translate/text for Somali -> Amharic...")
    payload_som = {
        "text": "Sidee tihiin? Caafimaadkiinna sidee yahay?",
        "src": "som",
        "tgt": "amh",
    }
    r_som = client.post("/translate/text", json=payload_som)
    data_som = r_som.json()
    print("Somali status:", r_som.status_code)
    print("Somali response:", data_som)
    assert r_som.status_code == 200
    assert data_som["is_tm_match"] is True
    assert "እንደምን" in data_som["translated_text"]

    print("\n✓ All API endpoint tests PASSED!")

if __name__ == "__main__":
    test_endpoints()
