# LISAN Project Inspection & Run Requirements Report

This report provides a comprehensive inspection of the **LISAN** project structure, core components, and the exact requirements needed to successfully run both the Python AI backend and the Flutter mobile application.

---

## 🏗️ Project Architecture Inspection

LISAN is structured into two main tiers:
1. **AI Backend (`ai_pipeline/` & `server.py`)**:
   - **FastAPI Server** (`server.py`): Exposes REST endpoints (`/translate/text`, `/translate/audio`, `/health`, `/languages`).
   - **Speech-to-Text**: OpenAI Whisper tiny model.
   - **Speech Repair & Normalization** (`speech_repair.py`): Cleans disfluencies and colloquial Ethiopian speech artifacts.
   - **Hybrid Smart Translator** (`smart_engine.py`): SQLite Translation Memory (Tier 1) + CTranslate2 / PyTorch NLLB-200 distilled 600M (Tier 2).

2. **Mobile Client (`ethiopian_translator/`)**:
   - Cross-platform **Flutter App** (Dart).
   - Audio recording (`record` / `flutter_sound`), REST client (`translator_api.dart`), and conversation UI.

---

## 📋 What is Needed to Run the Project

### 1. Python Backend Requirements
- **Python 3.11** (virtual environment at `.venv`).
- **Dependencies**: Installed via `pip install -r ai_pipeline/requirements.txt` (torch, transformers, fastapi, uvicorn, openai-whisper, etc.).
- **Backend Run Command**:
  ```powershell
  $env:PYTHONUTF8=1; .venv\Scripts\python -m uvicorn server:app --host 127.0.0.1 --port 8000
  ```

### 2. Flutter Frontend & Android Emulator Requirements
- **Flutter SDK** (v3.47.5 stable).
- **Android Emulator** (e.g. `emulator-5554` running API 34+).
- **ADB Port Forwarding** (so the emulator reaches the local FastAPI backend):
  ```powershell
  adb reverse tcp:8000 tcp:8000
  ```
- **Java & Gradle Compatibility Fix**:
  - *Current blocker*: The machine has **Java 25 (OpenJDK 25.0.3)** bundled in Android Studio JBR, while Gradle versions `<= 8.14` expect Java 21 or earlier.
  - *Required fix*: Configure Gradle/Flutter to use **JDK 17 or JDK 21** (or set `org.gradle.java.home` in `gradle.properties` to point to a JDK 21 installation once available).

---

## 🔍 Missing / Leftover Items to Complete

1. **JDK Version Alignment for Gradle Build**:
   - Ensure a compatible JDK (Java 17 or 21) is active for Gradle builds so the Android APK compiles without Java 25 compatibility errors.
2. **End-to-End Mobile Test**:
   - With backend running and `adb reverse` active, launch `flutter run -d emulator-5554` once Java/Gradle alignment is resolved.
