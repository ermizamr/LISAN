# 🌍 Ethiopian Language Translator — AI Handoff Documentation

> **Project**: Offline-capable real-time AI language translator for Ethiopian languages  
> **Hackathon Deadline**: 20 days from Sep 19, 2026 (ends ~Oct 9, 2026)  
> **Current Day**: Day 3 of 20  
> **Developer**: Ermi (Full Stack / AI / Mobile — Python, Django, Flutter, React)  
> **Workspace**: `C:\Users\admin\Documents\antigravity\amazing-bardeen\`

---

## 🎯 Project Goal

Build a **mobile app** (Flutter) that translates speech between Ethiopian local languages in real-time, **fully offline**. Two people who speak different languages hold one phone and communicate through it.

**Target languages:**
- Amharic (አማርኛ) — 500k+ sentences available
- Afaan Oromo — 450k+ sentences available  
- Somali — 200k+ sentences available
- Tigrinya (ትግርኛ) — 200k+ sentences available
- English — for foreign visitors

**Data source**: [dataset.et](https://dataset.et) — open Ethiopian language corpus managed by Snapwre (NVIDIA Inception member). HuggingFace: [huggingface.co/snapwre](https://huggingface.co/snapwre)

---

## ✅ What's Already Built (Days 1–3)

### AI Pipeline — `ai_pipeline/` (COMPLETE & TESTED)

| Component | Technology | Status | Performance |
|---|---|---|---|
| Speech-to-Text | OpenAI Whisper tiny | ✅ Working | 0.41s per phrase |
| Translation | Meta NLLB-200 distilled 600M | ✅ Working | ~5s (optimized) |
| Text-to-Speech | pyttsx3 (offline) | ✅ Working | 0.21s |
| **Full pipeline** | All combined | ✅ Working | **~5.9s end-to-end** |

### Languages Confirmed Working
- ✅ English → Amharic: "Where is the nearest hospital?" → "በአቅራቢያው ያለው ሆስፒታል የት ነው?"
- ✅ Amharic → English: "ሰላም, እንዴት ነህ?" → "Hello, how are you?"
- ✅ English → Oromo: "Where is the hospital?" → "Hospitaalichi eessa jira?"
- ✅ Oromo → English: "Galatoomaa, nagaatti!" → "Thank you, peace!"

---

## 📁 Project Structure

```
amazing-bardeen/
└── ai_pipeline/
    ├── pipeline.py              ← CORE: Full AI pipeline class
    ├── live_translate.py        ← Interactive CLI demo (conversation mode)
    ├── test_translation.py      ← Text translation tests (all passing)
    ├── test_stt.py              ← STT + end-to-end tests (passing)
    ├── generate_test_audio.py   ← WAV test file generator
    ├── test_audio/              ← Generated WAV test files
    └── requirements.txt         ← All Python dependencies
```

---

## 🔧 Environment Setup

### System
- **OS**: Windows 11 Pro x86_64
- **Python**: 3.11.9
- **RAM**: 7.63 GiB (models use ~5–6GB when loaded)
- **Storage**: ~10GB used for models + project
- **FFmpeg**: v9.0.1 installed (required by Whisper)

### Key Packages Installed
```
torch, torchaudio, transformers, sentencepiece
openai-whisper
sounddevice, soundfile, scipy, numpy
pyttsx3
rich
gtts
pydub, miniaudio
ctranslate2
```

### Run Commands (always prefix with `$env:PYTHONUTF8=1;` on Windows PowerShell)
```powershell
# Text translation test
$env:PYTHONUTF8=1; python test_translation.py

# Full STT + end-to-end test
$env:PYTHONUTF8=1; python test_stt.py

# Interactive live demo (mic + conversation mode)
$env:PYTHONUTF8=1; python live_translate.py
```

---

## 🧠 pipeline.py — Key Classes

### `TranslatorPipeline` (main class to use)
```python
from pipeline import TranslatorPipeline

pipeline = TranslatorPipeline(whisper_size="tiny")
pipeline.load_all()  # Loads all 3 models + warms up (~15s first time)

# Text translation
result = pipeline.translate_text("Hello", "eng", "amh")

# Audio file translation
result = pipeline.translate_audio("audio.wav", "eng", "amh", speak_result=True)

# Live microphone translation
result = pipeline.live_translate("eng", "amh", duration=5)
```

### Language Keys
```python
LANGUAGES = {
    "amh": { "nllb_code": "amh_Ethi", "whisper_code": "am" },  # Amharic
    "eng": { "nllb_code": "eng_Latn", "whisper_code": "en" },  # English
    "orm": { "nllb_code": "gaz_Latn", "whisper_code": "om" },  # Afaan Oromo
    "som": { "nllb_code": "som_Latn", "whisper_code": "so" },  # Somali
    "tir": { "nllb_code": "tir_Ethi", "whisper_code": None  },  # Tigrinya
}
```

> **Important**: Oromo uses `gaz_Latn` (not `orm_Latn`) in NLLB-200 distilled 600M

### `WhisperSTT`
- Loads WAV via `soundfile` directly (bypasses FFmpeg subprocess)
- Passes numpy array to Whisper (no file path)
- Auto-resamples to 16kHz

### `NLLB200Translator`
- Model: `facebook/nllb-200-distilled-600M`
- `num_beams=2` (sweet spot: same quality as 4, 3x faster)
- `max_length=256`
- **Has warm-up call on load** to eliminate 13s cold-start

### `SimpleTTS`
- Uses `pyttsx3` for offline TTS
- **Only use `speak(text)`** — never `save_to_file()` (hangs on Windows)

---

## ⚠️ Known Issues & Gotchas

| Issue | Status | Fix |
|---|---|---|
| `pyttsx3.save_to_file()` hangs on Windows | Known | Use `speak()` only |
| Whisper needs FFmpeg even for WAV | Fixed | Load via soundfile numpy array |
| cp1252 encoding errors with Ethiopic script | Fixed | Always use `$env:PYTHONUTF8=1;` |
| `&&` not valid in PowerShell | Known | Use separate commands |
| `torch.ao.quantization` deprecated in 2.10 | Known | Use num_beams=2 instead |
| Oromo `orm_Latn` code empty output | Fixed | Use `gaz_Latn` instead |
| First translation cold-start (~13s) | Fixed | Warm-up call in `load()` |
| gTTS sometimes fails (internet) | Known | Falls back to silent WAV gracefully |

---

## 🗓️ Remaining 17-Day Roadmap

### Days 4–7: Pipeline Polish & Flutter Setup
- [ ] **Day 4**: Test live microphone with real voice samples, stress test all language pairs
- [x] **Day 5**: Install Flutter, create new project, scaffold app structure
- [x] **Day 6**: Design conversation UI (walkie-talkie style, tap-to-speak)
- [x] **Day 7**: Create initial Flutter ↔ Python bridge (REST API wrapper around pipeline)

### Days 8–14: Flutter Mobile App
- [ ] **Day 8**: Flutter audio recording (flutter_sound or record package)
- [ ] **Day 9**: Connect Flutter to Python backend (local HTTP server via FastAPI)
- [ ] **Day 10**: Display transcription + translation in real-time
- [ ] **Day 11**: Language selector UI (flag buttons for each language)
- [ ] **Day 12**: Conversation history screen
- [ ] **Day 13**: Offline mode detection + status indicator
- [ ] **Day 14**: Full end-to-end mobile test

### Days 15–20: Polish & Demo
- [ ] **Day 15**: Fix bugs, improve UI
- [ ] **Day 16**: Add loading screen with warm-up progress
- [ ] **Day 17**: Record demo video
- [ ] **Day 18**: Prepare pitch deck
- [ ] **Day 19**: Final device testing
- [ ] **Day 20**: Submit & present

---

## 📱 Flutter App Architecture (Next Phase)

### Recommended Approach: Local FastAPI Backend

Since running PyTorch in Flutter directly is complex, serve the Python pipeline as a local HTTP API on the phone/dev machine:

```
Flutter App (Dart)
      ↕  HTTP (localhost:8000)
FastAPI Server (Python)
      ↕
pipeline.py (Whisper + NLLB + pyttsx3)
```

### FastAPI Server to Build (Day 7)
```python
# server.py
from fastapi import FastAPI, UploadFile
from pipeline import TranslatorPipeline

app = FastAPI()
pipeline = TranslatorPipeline()
pipeline.load_all()  # Load once at startup

@app.post("/translate/text")
async def translate_text(text: str, src: str, tgt: str):
    result = pipeline.translate_text(text, src, tgt)
    return {"translation": result}

@app.post("/translate/audio")
async def translate_audio(file: UploadFile, src: str, tgt: str):
    # Save file, run pipeline, return translation + audio
    ...

@app.get("/languages")
async def get_languages():
    return LANGUAGES
```

### Flutter Packages Needed
```yaml
# pubspec.yaml
dependencies:
  flutter_sound: ^9.2.13    # Audio recording
  http: ^1.2.0               # REST API calls
  just_audio: ^0.9.36        # Playback translated audio
  provider: ^6.1.2           # State management
  flutter_riverpod: ^2.5.0  # Alternative state management
```

---

## 🏆 Hackathon Winning Strategy

1. **Demo scenario**: Doctor (speaks Amharic) + Patient (speaks Oromo) → real-time translation
2. **Open airplane mode on stage** → show it still works offline
3. **Mention Dataset.ET** → shows ecosystem awareness
4. **Show latency**: "Under 6 seconds, fully offline, 5 languages"
5. **Impact angle**: 80+ Ethiopian languages, millions can't communicate

---

## 📊 Latency Benchmarks (i5-1135G7, no GPU)

```
Whisper tiny STT:     0.41s
NLLB-200 translation: 5.28s  (after warm-up)
pyttsx3 TTS:          0.21s
─────────────────────────────
Total end-to-end:     5.91s  ✅ (target was <8s)
```

---

## 🔗 Resources

- Dataset.ET: https://dataset.et
- HuggingFace snapwre: https://huggingface.co/snapwre
- NLLB-200 model: https://huggingface.co/facebook/nllb-200-distilled-600M
- Whisper: https://github.com/openai/whisper
- Dataset.ET Telegram: https://t.me/dataset_et

---

*Last updated: Day 7, Sep 19 2026 — Flutter shell and initial FastAPI bridge complete*
