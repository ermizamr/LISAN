# 🤖 AI ASSISTANT PROMPT — LISAN (ልሳን) PROJECT & GPU TRAINING

## 🎯 Context
You are working on **LISAN (ልሳን)**, a high-performance offline speech-to-speech translation system for Ethiopian and Horn of Africa languages:
- **Amharic (አማርኛ)**
- **Afaan Oromo**
- **Tigrinya (ትግርኛ)**
- **Somali (Soomaali)**
- **English**

The project combines:
1. **STT (Speech-to-Text)**: Native Wav2Vec2-BERT models (`snapwre/hohe-asr-amharic`, `badrex/Ethio-ASR-multilingual-600M`) with lexicon beam search + OpenAI Whisper.
2. **NMT (Machine Translation)**: Meta NLLB-200 distilled 600M fine-tuned on Ethiopian corpora + CTranslate2 INT8 quantization + SQLite Translation Memory.
3. **TTS (Text-to-Speech)**: Meta MMS-TTS neural voice synthesis (`facebook/mms-tts-*`) + Piper TTS.
4. **Mobile Client**: Flutter application with offline voice-to-voice translation.

---

## ⚡ WORKING ON A GAMING PC (GPU TRAINING & FINE-TUNING)

If you are running on an NVIDIA GPU gaming PC to train or fine-tune models, **READ THIS FIRST**:
👉 **[`AGENT_TRAINING_RUNBOOK.md`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/AGENT_TRAINING_RUNBOOK.md)**
👉 **[`RESOURCES_CATALOG.md`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/RESOURCES_CATALOG.md)**

### 1-Minute GPU Quickstart
```powershell
# 1. Force UTF-8 encoding in PowerShell
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 2. Automated environment setup (Installs PyTorch with CUDA 12.1 + dependencies)
powershell -ExecutionPolicy Bypass -File .\setup_training_env.ps1

# 3. Check GPU acceleration & get auto-tuned hyperparameters
python scripts/check_gpu_env.py

# 4. Run automated training & optimization pipeline
python scripts/run_all_training.py --all
```

### Key Training Commands by Pillar:
- **Translation (NMT)**:
  ```powershell
  python scripts/train_nllb_lora.py --batch_size 16 --grad_accum 2 --merge_and_export --eval_benchmarks
  ```
  *Trains on 68,000+ pairs in `data/training_data/`, merges LoRA weights, and exports to `models_optimized/nllb_int8`.*
- **Speech-to-Text (STT)**:
  ```powershell
  python scripts/prepare_stt_data.py --source fleurs
  python scripts/train_whisper_lora.py --base_model openai/whisper-small --batch_size 8 --grad_accum 4 --merge_and_save
  python scripts/evaluate_stt.py
  ```
- **Text-to-Speech (TTS)**:
  ```powershell
  python scripts/benchmark_tts.py
  ```

---

## ⚠️ Critical Rules & Gotchas
1. **Always set `$env:PYTHONUTF8=1;`** in PowerShell before any Python command (prevents CP1252 crash on Ethiopic text).
2. **Never call `pyttsx3.save_to_file()` on Windows** — it hangs the SAPI5 COM loop. Always use `.speak()` or Meta MMS-TTS.
3. **NLLB Language Codes**:
   - Afaan Oromo: `gaz_Latn` (NOT `orm_Latn`!)
   - Amharic: `amh_Ethi`
   - Tigrinya: `tir_Ethi`
   - Somali: `som_Latn`
   - English: `eng_Latn`
4. **PyTorch with CUDA**: On Windows, always install PyTorch with the CUDA wheel:
   `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`
5. **BitsAndBytes on Windows**: Use `bitsandbytes>=0.43.0` for native Windows 64-bit CUDA support.
6. **Separate PowerShell commands**: The `&&` operator is not valid in legacy PowerShell; run commands on separate lines or with `;`.

---

## 📁 Key File Locations
- Core Pipeline: [`ai_pipeline/pipeline.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/ai_pipeline/pipeline.py)
- Hybrid Smart Engine: [`ai_pipeline/smart_engine.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/ai_pipeline/smart_engine.py)
- Speech Repair & Healing: [`ai_pipeline/speech_repair.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/ai_pipeline/speech_repair.py)
- FastAPI Server: [`server.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/server.py)
- Parallel Training Data: [`data/training_data/`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/data/training_data/)
- Translation Memory DB: [`data/translation_memory.db`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/data/translation_memory.db)
- Lexicon Unigrams: [`data/lexicon/`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/data/lexicon/)
