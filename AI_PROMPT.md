# AI ASSISTANT PROMPT — Ethiopian Language Translator Hackathon

## Context
I am building an offline AI-based real-time language translator for Ethiopian languages as a hackathon project (20-day deadline). We are on Day 3 of 20.

## What's Already Done
The Python AI pipeline is COMPLETE and tested:
- **Whisper tiny** for speech-to-text (0.41s, 100% accuracy)
- **NLLB-200 distilled 600M** for translation (~5s, Amharic/Oromo/English/Somali/Tigrinya)
- **pyttsx3** for text-to-speech (0.21s)
- **Total latency: 5.91s end-to-end, fully offline**

All code is in: `C:\Users\admin\Documents\antigravity\amazing-bardeen\ai_pipeline\`

## Read First
Before doing anything, read this file completely:
`C:\Users\admin\Documents\antigravity\amazing-bardeen\HANDOFF.md`

It contains:
- Full architecture overview
- All known issues and their fixes
- Language codes (IMPORTANT: Oromo uses gaz_Latn not orm_Latn)
- Windows-specific gotchas (pyttsx3, PowerShell, UTF-8)
- Remaining 17-day roadmap

## What To Do Next (Day 4)

### Step 1: Test live microphone with real voice
```powershell
cd C:\Users\admin\Documents\antigravity\amazing-bardeen\ai_pipeline
$env:PYTHONUTF8=1; python live_translate.py
# Choose option 2 (single phrase) or 3 (conversation mode)
# Test: speak English, hear Amharic
# Test: speak Amharic, hear English
```

### Step 2: If mic works, start Flutter app (Day 5)
```powershell
# Check Flutter is installed
flutter --version

# If not installed:
# Download from https://flutter.dev/docs/get-started/install/windows
# Add to PATH: C:\flutter\bin

# Create the app
flutter create ethiopian_translator
cd ethiopian_translator
```

### Step 3: Build FastAPI bridge (Day 7)
Create `C:\Users\admin\Documents\antigravity\amazing-bardeen\server.py`
```python
pip install fastapi uvicorn python-multipart
# Then build REST API wrapping the pipeline
```

## Critical Rules
1. **Always use `$env:PYTHONUTF8=1;`** before any Python command in PowerShell
2. **Never call `pyttsx3.save_to_file()`** — it hangs on Windows. Only use `.speak()`
3. **Oromo NLLB code is `gaz_Latn`** not `orm_Latn`
4. **Whisper loads audio via soundfile numpy array** — not file path (FFmpeg bypass)
5. **Use separate PowerShell commands** — `&&` is not valid in PowerShell

## Key File: pipeline.py
The main class is `TranslatorPipeline`. Import and use like this:
```python
from pipeline import TranslatorPipeline
pipeline = TranslatorPipeline(whisper_size="tiny")
pipeline.load_all()  # ~15s including warm-up
result = pipeline.translate_text("Hello", "eng", "amh")
result = pipeline.live_translate("eng", "amh", duration=5)
```
