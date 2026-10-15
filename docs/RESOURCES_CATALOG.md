# 📚 LISAN AI — COMPREHENSIVE RESOURCES CATALOG

This catalog indexes every dataset, model checkpoint, lexicon unigram list, benchmark suite, and training asset available in the **LISAN** project.

---

## 1. Machine Translation (NMT) Resources

### A. Pre-packaged Parallel Training Corpora (`data/training_data/`)
Ready for immediate fine-tuning with PyTorch, Hugging Face `datasets`, and `peft`:

| File | Size | Samples | Description |
|---|---|---|---|
| [`train.jsonl`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/data/training_data/train.jsonl) | 42.84 MB | **107,784** | 95% stratified split across all 20 language pairs |
| [`val.jsonl`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/data/training_data/val.jsonl) | 2.26 MB | **5,672** | 5% stratified validation split |
| [`metadata.json`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/data/training_data/metadata.json) | 720 bytes | **113,456** total | Pair counts, FLORES codes, and schema metadata |

#### Language Pair Breakdown:
- **Oromo $\leftrightarrow$ Amharic**: **16,000** pairs (`orm->amh`: 8,000, `amh->orm`: 8,000)
- **Tigrinya $\leftrightarrow$ Amharic**: **16,000** pairs (`tir->amh`: 8,000, `amh->tir`: 8,000)
- **Somali $\leftrightarrow$ Amharic**: **16,000** pairs (`som->amh`: 8,000, `amh->som`: 8,000)
- **Oromo $\leftrightarrow$ Tigrinya**: **16,000** pairs (`orm->tir`: 8,000, `tir->orm`: 8,000)
- **Oromo $\leftrightarrow$ Somali**: **16,000** pairs (`orm->som`: 8,000, `som->orm`: 8,000)
- **Somali $\leftrightarrow$ Tigrinya**: **16,000** pairs (`som->tir`: 8,000, `tir->som`: 8,000)
- **English $\leftrightarrow$ Amharic**: 4,382 pairs (`eng->amh`: 2,191, `amh->eng`: 2,191)
- **English $\leftrightarrow$ Oromo**: 4,362 pairs (`eng->orm`: 2,178, `orm->eng`: 2,184)
- **English $\leftrightarrow$ Tigrinya**: 4,362 pairs (`eng->tir`: 2,181, `tir->eng`: 2,181)
- **English $\leftrightarrow$ Somali**: 4,350 pairs (`eng->som`: 2,175, `som->eng`: 2,175)

### B. Translation Memory Database (`data/translation_memory.db`)
- **Format**: SQLite 3 with FTS5 Full-Text Search.
- **Size**: **52.7 MB**.
- **Coverage**: Pre-indexed conversational phrases, idioms, greetings, healthcare questions, kebele administration terms, market negotiations, police dialogue, and banking scenarios.
- **Confidence Scoring**: 0.75 to 1.0 confidence-rated entries.

### C. Raw Parallel Bitext (`data/raw_bitext/`)
Unfiltered source corpora available for scaling up:
- `amharic-oromo.csv`: 15.33 MB
- `amharic-somali.csv`: 125.85 MB
- `amharic-tigrinya.csv`: 70.17 MB
- `oromo-somali.csv`: 9.77 MB
- `oromo-tigrinya.csv`: 8.56 MB
- `somali-tigrinya.csv`: 31.96 MB

### D. HornMT Benchmark Suite (`data/hornmt/` and `data/benchmarks/`)
- Reference multi-parallel test sentences across Amharic, Afaan Oromo, Tigrinya, Somali, and English.
- Evaluated with BLEU, chrF++, and sentence accuracy via `scripts/evaluate_benchmarks.py`.

---

## 2. Speech-to-Text (STT) Resources

### A. Model Architectures & Hugging Face Hub IDs

| Model Engine | Hugging Face ID | Architecture | Targeted Languages |
|---|---|---|---|
| **Hohe ASR** | `snapwre/hohe-asr-amharic` | Wav2Vec2-BERT 600M | **Amharic** (16.1% WER) |
| **Ethio Multilingual ASR** | `badrex/Ethio-ASR-multilingual-600M` | Wav2Vec2-BERT 600M | **Amharic, Afaan Oromo, Tigrinya** |
| **Dedicated Oromo ASR** | `badrex/Ethio-ASR-oromo` | Wav2Vec2-BERT 600M | **Afaan Oromo** |
| **OpenAI Whisper** | `openai/whisper-tiny` / `whisper-small` | Encoder-Decoder Transformer | **English, Somali**, Multilingual |

### B. Lexicon-Guided CTC Beam Search Decoders (`data/lexicon/`)
Language-isolated unigram frequency vocabularies used with `pyctcdecode` to eliminate cross-language / cross-script confusion:
- `amh_unigrams.txt`: 222 KB (Amharic vocabulary)
- `orm_unigrams.txt`: 894 KB (Afaan Oromo Qubee vocabulary)
- `tir_unigrams.txt`: 1.90 MB (Tigrinya vocabulary)
- `som_unigrams.txt`: 1.63 MB (Somali vocabulary)

### C. Audio Evaluation & Test Recordings
- `ai_pipeline/test_audio/hello_en.wav`: "Hello, how are you today?" (16kHz mono)
- `ai_pipeline/test_audio/hospital_en.wav`: "Where is the nearest hospital?" (16kHz mono)
- `ai_pipeline/test_audio/doctor_en.wav`: "I need to see a doctor immediately." (16kHz mono)
- `test_speech.wav`: "ሰላም እንደምን አደራችሁ" (Amharic morning greeting)
- `test_oromo_tts.wav`: "Akkam jirtu nagaa dhaa" (Oromo greeting)
- `real_test1.wav` to `real_test5.wav`: Real smartphone microphone recordings in noisy environments.
- `real_user1.wav` to `real_user3.wav`: Authenticated speaker samples.
- `test_user_2443.wav`, `test_user_2490.wav`, `test_user_2533.wav`: Conversational voice clips.

---

## 3. Text-to-Speech (TTS) Resources

### A. Meta MMS-TTS Neural Voice Checkpoints

| Language | Model Hub ID | VITS Architecture | Sample Rate |
|---|---|---|---|
| **Amharic** | `facebook/mms-tts-amh` | VITS Neural Vocoder | 16,000 Hz |
| **Afaan Oromo** | `facebook/mms-tts-orm` / `facebook/mms-tts-gaz` | VITS Neural Vocoder | 16,000 Hz |
| **Tigrinya** | `facebook/mms-tts-tir` | VITS Neural Vocoder | 16,000 Hz |
| **Somali** | `facebook/mms-tts-som` | VITS Neural Vocoder | 16,000 Hz |
| **English** | `facebook/mms-tts-eng` | VITS Neural Vocoder | 16,000 Hz |

### B. High-Speed Local TTS
- `piper-tts`: Fast C++ / ONNX-based neural TTS for on-device synthesis with RTF $< 0.1\times$.
- `pyttsx3`: Native Windows SAPI5 offline fallback.

---

## 4. Key Scripts & Automation Tools

| Script | Purpose |
|---|---|
| [`scripts/check_gpu_env.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/scripts/check_gpu_env.py) | GPU diagnostics, CUDA verification, VRAM hyperparameter tuning |
| [`scripts/train_nllb_lora.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/scripts/train_nllb_lora.py) | NLLB-200 QLoRA fine-tuning, LoRA merging, CTranslate2 INT8 export |
| [`scripts/prepare_stt_data.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/scripts/prepare_stt_data.py) | Downloads & pre-processes FLEURS / Common Voice speech corpora |
| [`scripts/train_whisper_lora.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/scripts/train_whisper_lora.py) | Whisper LoRA fine-tuning for Ethiopian speech |
| [`scripts/evaluate_stt.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/scripts/evaluate_stt.py) | STT latency, accuracy, and WER evaluation |
| [`scripts/benchmark_tts.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/scripts/benchmark_tts.py) | TTS synthesis speed, Real-Time Factor (RTF), and audio checks |
| [`scripts/run_all_training.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/scripts/run_all_training.py) | Master orchestrator to run all training tasks end-to-end |
| [`scripts/evaluate_benchmarks.py`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/scripts/evaluate_benchmarks.py) | Measures BLEU / chrF++ on HornMT test sets |
| [`setup_training_env.ps1`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/setup_training_env.ps1) | PowerShell 1-click CUDA and dependency installer |
| [`setup_training_env.bat`](file:///c:/Users/admin/Documents/antigravity/amazing-bardeen/setup_training_env.bat) | Batch 1-click installer for Command Prompt |

---

## 5. External Hub & Dataset Portals
- **Dataset.ET**: Open Ethiopian Language Corpus ([https://dataset.et](https://dataset.et))
- **Snapwre Hugging Face**: [https://huggingface.co/snapwre](https://huggingface.co/snapwre)
- **Badrex Hugging Face**: [https://huggingface.co/badrex](https://huggingface.co/badrex)
- **Meta NLLB-200**: [https://huggingface.co/facebook/nllb-200-distilled-600M](https://huggingface.co/facebook/nllb-200-distilled-600M)
- **Meta MMS**: [https://huggingface.co/facebook/mms-tts](https://huggingface.co/facebook/mms-tts)
- **Google FLEURS**: [https://huggingface.co/datasets/google/fleurs](https://huggingface.co/datasets/google/fleurs)
- **Mozilla Common Voice**: [https://commonvoice.mozilla.org](https://commonvoice.mozilla.org)
