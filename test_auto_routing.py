import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import whisper

model = whisper.load_model("tiny")

def detect_audio_language(audio_path: str, pair: tuple[str, str]) -> str | None:
    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio)
    _, probs = model.detect_language(mel)
    if "eng" in pair:
        en_prob = probs.get("en", 0.0)
        top = max(probs, key=probs.get)
        print(f"[{audio_path}] en_prob={en_prob:.3f}, top={top}")
        if en_prob > 0.35:
            return "eng"
        else:
            other = pair[0] if pair[1] == "eng" else pair[1]
            return other
    return None

test_files = [
    ("real_test1.wav", "Amharic (Selam)"),
    ("real_test2.wav", "Amharic (Salam)"),
    ("real_test3.wav", "Amharic (Long sentence)"),
    ("real_test4.wav", "Amharic (Visit Ethiopia)"),
    ("real_test5.wav", "English (What are you talking about...)"),
]

for f, desc in test_files:
    det = detect_audio_language(f, ("amh", "eng"))
    print(f"File: {f} ({desc}) => Auto-detected: {det}\n")
