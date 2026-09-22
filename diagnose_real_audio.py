import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import TranslatorPipeline

pipeline = TranslatorPipeline()
pipeline.load_all()

audio_files = ["real_test1.wav", "real_test2.wav", "real_test3.wav"]

print("=" * 70)
for audio_file in audio_files:
    if not os.path.exists(audio_file):
        print(f"Missing {audio_file}")
        continue
        
    size = os.path.getsize(audio_file)
    print(f"\n--- Analyzing {audio_file} ({size} bytes) ---")
    
    # 1. Test Whisper (English)
    try:
        whisper_en = pipeline.stt.transcribe(audio_file, "en")
        print(f"Whisper (EN) transcription: '{whisper_en}'")
    except Exception as e:
        print(f"Whisper (EN) error: {e}")
        
    # 2. Test Whisper (Amharic)
    try:
        whisper_am = pipeline.stt.transcribe(audio_file, "am")
        print(f"Whisper (AM) transcription: '{whisper_am}'")
    except Exception as e:
        print(f"Whisper (AM) error: {e}")

    # 3. Test Hohe ASR (Amharic)
    try:
        hohe_am = pipeline.hohe_stt.transcribe(audio_file)
        print(f"Dataset.ET Hohe ASR transcription: '{hohe_am}'")
    except Exception as e:
        print(f"Hohe ASR error: {e}")

print("\n" + "=" * 70)
