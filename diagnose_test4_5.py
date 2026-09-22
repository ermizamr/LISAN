import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import TranslatorPipeline

pipeline = TranslatorPipeline()
pipeline.load_all()

for fname in ["real_test4.wav", "real_test5.wav"]:
    print(f"\n================ {fname} ================")
    try:
        w_en = pipeline.stt.transcribe(fname, "en")
        print(f"Whisper EN: '{w_en}'")
    except Exception as e:
        print(f"Whisper EN error: {e}")
        
    try:
        hohe = pipeline.hohe_stt.transcribe(fname)
        print(f"Dataset.ET Hohe: '{hohe}'")
        tr = pipeline.translate_text(hohe, "amh", "eng")
        print(f"Translation (Amh->Eng): '{tr}'")
    except Exception as e:
        print(f"Hohe error: {e}")
