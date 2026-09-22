import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import TranslatorPipeline

p = TranslatorPipeline()
p.translator.load()

noisy_cases = [
    # 1. Stutters, hesitations, noise
    ("amh", "eng", "እ... ሰላም ሰላም እንዴት ነህ"),
    ("amh", "eng", "ሀ ሀ ሆስፒታል የት"),
    ("amh", "eng", "አ... ውሃ እፈልጋ"),
    ("amh", "eng", "ወደ ኢትዮጵያ መትታቃለህ?"),
    ("amh", "eng", "አይደል ወንድሜ"),
    ("amh", "eng", "ይቅር"),
    ("amh", "eng", "አመሰግ"),
    
    # 2. Colloquial Amharic that often trips up translation
    ("amh", "eng", "ምነው ዝም አልክ?"),
    ("amh", "eng", "ደህና ሁን ወንድሜ"),
    ("amh", "eng", "ምን ፈልገህ ነው?"),
    ("amh", "eng", "የት ልሂድ?"),
    ("amh", "eng", "ታክሲ የት ይገኛል?"),
    ("amh", "eng", "ዋጋው ውድ ነው"),
    ("amh", "eng", "ቅናሽ አድርግልኝ"),
    ("amh", "eng", "እባክህ እርዳኝ"),
    
    # 3. English colloquial / interrupted -> Amharic
    ("eng", "amh", "uh... where is... where is the hospital"),
    ("eng", "amh", "haha how much is it"),
    ("eng", "amh", "can you give me a discount?"),
    ("eng", "amh", "where can I find a taxi?"),
    ("eng", "amh", "it is too expensive"),
    ("eng", "amh", "what are you doing?"),
    ("eng", "amh", "see you tomorrow!"),
]

print("=" * 60)
for src, tgt, text in noisy_cases:
    out = p.translate_text(text, src, tgt)
    print(f"[{src} -> {tgt}] '{text}'\n  => '{out}'\n")
print("=" * 60)
