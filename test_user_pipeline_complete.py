import sys
import os
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai_pipeline.pipeline import TranslatorPipeline

print("Initializing TranslatorPipeline (100% offline)...")
pipeline = TranslatorPipeline()
pipeline.load_all()

files = [
    ("real_user1.wav", "amh", "eng", "Test 1: User said 'ሰላም እንዴት ነህ'"),
    ("real_user2.wav", "amh", "eng", "Test 2: User said 'ሰላም ነው እንዴት ነህ እኔ በጣም ደህና ነኝ አመሰግናለው'"),
    ("real_user3.wav", "amh", "eng", "Test 3: User monologue with 'በናትህ', 'አስቤ አላውቅም', cities & countries"),
]

for audio_path, src, tgt, desc in files:
    print(f"\n==================================================")
    print(f"Running: {desc}")
    print(f"Audio: {audio_path}")
    t0 = time.perf_counter()
    result = pipeline.translate_audio(audio_path, src, tgt, speak_result=False)
    dt = round(time.perf_counter() - t0, 2)
    print(f"Repaired Source:  '{result['source_text']}'")
    print(f"Clean Translated: '{result['translated_text']}'")
    print(f"Total Time:       {dt}s")
print("==================================================")
