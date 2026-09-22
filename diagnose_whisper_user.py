import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import whisper
import soundfile as sf
import numpy as np

print("Loading Whisper tiny...")
model = whisper.load_model("tiny")

files = [
    ("real_user1.wav", "Expected: ሰላም እንዴት ነህ"),
    ("real_user2.wav", "Expected: ሰላም ነው እንዴት ነህ እኔ በጣም ደህና ነኝ አመሰግናለው"),
    ("real_user3.wav", "Expected: ሀገሩ እንዴት ነው በናትህ ይህ ሀገር በጣም ደስ የሚል ሀገር ነው እኔ ይሄ ሀገር በጣም ደስ ይላል ብዬ አስቤ አላውቅም አንተ ግን ስለዚች ሀገር ስለዚህ ሀገር ስለዚህ ሀገርና ስለ እነዚህ ሀገራት ምን ታስባለህ"),
]

for filename, expected in files:
    print(f"\n==================== {filename} ====================")
    print(expected)
    audio, sr = sf.read(filename, dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000:
        import scipy.signal as sig
        audio = sig.resample(audio, int(len(audio)*16000/sr))
        
    res_am = model.transcribe(audio, language="am", fp16=False)
    print(f"Whisper (Amharic): '{res_am['text'].strip()}'")
