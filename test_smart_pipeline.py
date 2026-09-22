"""Test script for speech-repair and smart translation pipeline."""

from ai_pipeline.pipeline import TranslatorPipeline

def run_tests():
    p = TranslatorPipeline()
    p.translator.load()
    
    test_cases = [
        ("ሰላም እንዴት ነው", "amh", "eng"),
        ("ሳላም", "amh", "eng"),
        ("ሰላም ሰላም እንዴት ነህ ሀ ሀ", "amh", "eng"),
        ("ሆስፒታል የት", "amh", "eng"),
        ("ወደ ኢትዮጵያ መትታቃለህ በሆነ አጋጣሚ መተልታቅ ትችላለህ", "amh", "eng"),
        ("ውሃ መጠጣት እፈልጋለሁ", "amh", "eng"),
        ("akkam jirtu", "orm", "eng"),
        ("ከመይ ኣለኻ", "tir", "eng"),
        ("iska warran", "som", "eng"),
    ]
    
    print("=" * 60)
    print("Testing Smart Translation Pipeline (Speech Repair + Offline Engine)")
    print("=" * 60)
    for text, src, tgt in test_cases:
        res = p.translate_text(text, src, tgt)
        print(f"[{src}->{tgt}] '{text}'\n  ==> '{res}'\n")

if __name__ == "__main__":
    run_tests()
