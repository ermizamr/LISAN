import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import TranslatorPipeline, LANGUAGES

p = TranslatorPipeline()
p.translator.load()

test_cases = [
    # English -> Amharic
    ("eng", "amh", "How are you?"),
    ("eng", "amh", "Where is the hospital?"),
    ("eng", "amh", "I want to drink water."),
    ("eng", "amh", "What is your name?"),
    ("eng", "amh", "Thank you very much."),
    ("eng", "amh", "Have you ever visited Ethiopia?"),
    ("eng", "amh", "I don't understand what you are saying."),
    ("eng", "amh", "Can you help me find a hotel?"),
    
    # Amharic -> English
    ("amh", "eng", "ሰላም እንዴት ነህ?"),
    ("amh", "eng", "ሆስፒታል የት ነው?"),
    ("amh", "eng", "ወደ ኢትዮጵያ መጥተህ ታውቃለህ?"),
    ("amh", "eng", "ውሃ መጠጣት እፈልጋለሁ"),
    ("amh", "eng", "ምን እያልክ እንደሆነ አልገባኝም"),
    ("amh", "eng", "እንደምን አደርክ"),
    ("amh", "eng", "ደህና እደር"),
    ("amh", "eng", "መርዳት ትችላለህ?"),
    
    # Afaan Oromo -> English & English -> Afaan Oromo
    ("orm", "eng", "akkam jirtu?"),
    ("eng", "orm", "How are you?"),
    ("eng", "orm", "Where is the hospital?"),
    
    # Tigrinya -> English & English -> Tigrinya
    ("tir", "eng", "ከመይ ኣለኻ?"),
    ("eng", "tir", "How are you?"),
    ("eng", "tir", "Where is the hospital?"),
]

print("=" * 60)
for src, tgt, text in test_cases:
    out = p.translate_text(text, src, tgt)
    print(f"[{src} -> {tgt}] '{text}'\n  => '{out}'\n")
print("=" * 60)
