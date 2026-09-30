# 🚀 LISAN AI — AGENT TRAINING RUNBOOK & GPU EXECUTION GUIDE

> **Target Audience**: AI Coding Assistant (Antigravity / Gemini / Cursor / Claude) or Developer operating on the NVIDIA GPU Gaming PC.  
> **Mission**: Fine-tune and export high-performance, offline-ready models for **STT (Speech-to-Text)**, **Machine Translation (NMT)**, and **TTS (Text-to-Speech)** for Ethiopian & Horn of Africa languages:
> - **Amharic (አማርኛ)**
> - **Afaan Oromo**
> - **Tigrinya (ትግርኛ)**
> - **Somali (Soomaali)**
> - **English**

---

## ⚡ The First 60 Seconds Checklist

When opening this repository on the gaming PC, execute these steps immediately in Windows PowerShell:

```powershell
# 1. Force UTF-8 encoding in PowerShell (MANDATORY for Ethiopic & Qubee scripts)
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 2. Navigate to project root
cd C:\Users\<Username>\Documents\LISAN  # or path to cloned repo

# 3. Pull latest commits from GitHub
git pull origin main

# 4. Run automated environment setup
powershell -ExecutionPolicy Bypass -File .\setup_training_env.ps1
```

If using Command Prompt (`cmd.exe`):
```bat
setup_training_env.bat
```

---

## 🖥️ Step 1: GPU Diagnostics & Pre-flight Check

Run the diagnostics script to inspect the NVIDIA GPU, verify CUDA drivers, test tensor memory allocation, and get auto-tuned hyperparameters:

```powershell
$env:PYTHONUTF8=1; python scripts/check_gpu_env.py
```

### Expected Output Checklist:
- [x] `PyTorch Version`: Must have `+cu121` or `+cu124` (NOT `+cpu`).
- [x] `CUDA Available`: Must show `✓ YES`.
- [x] `GPU Model`: Identifies your card (e.g. RTX 3060, RTX 3070, RTX 3080, RTX 4070, RTX 4090).
- [x] `VRAM Available`: Shows memory in GB.
- [x] `BitsAndBytes`: Must show `✓ Installed` (required for 4-bit QLoRA).
- [x] `CTranslate2`: Must show `✓ Installed`.

> [!CAUTION]
> If `CUDA Available` shows `✗ NO (Running on CPU)`, PyTorch was installed without CUDA support. Fix it immediately by running:
> ```powershell
> pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
> ```

---

## ⚙️ GPU VRAM Tuning Matrix

Adjust batch sizes and quantization according to the GPU's physical VRAM:

| GPU Tier | Example Cards | VRAM | NMT LoRA Batch | Grad Accum | STT Whisper Base | Quantization |
|---|---|---|---|---|---|---|
| **Entry / Laptop** | RTX 3050, RTX 2060, RTX 3060 Laptop | 6GB – 8GB | `8` | `4` | `openai/whisper-tiny` or `base` | 4-bit QLoRA |
| **Mid Tier** | RTX 3060 12GB, RTX 3080 10GB, RTX 4070 12GB | 10GB – 12GB | `16` | `2` | `openai/whisper-small` | 4-bit QLoRA |
| **High Tier** | RTX 3090 24GB, RTX 4080 16GB, RTX 4090 24GB | 16GB – 24GB | `32` | `1` | `openai/whisper-small` / `medium` | 4-bit / 8-bit / BF16 |

---

## 🌐 Step 2: Machine Translation (NMT) Fine-Tuning

### Goal:
Fine-tune Meta `facebook/nllb-200-distilled-600M` with LoRA on **113,456** curated Ethiopian and inter-local sentence pairs, merge the LoRA weights, and convert directly to **CTranslate2 INT8** for sub-100ms offline CPU/GPU inference.

### Dataset Ready in Repository:
- Train set: `data/training_data/train.jsonl` (**107,784** pairs)
- Validation set: `data/training_data/val.jsonl` (**5,672** pairs)
- Massive inter-local representation: **16,000** pairs each for Oromo $\leftrightarrow$ Amharic, Tigrinya $\leftrightarrow$ Amharic, Somali $\leftrightarrow$ Amharic, Oromo $\leftrightarrow$ Tigrinya, Oromo $\leftrightarrow$ Somali, Somali $\leftrightarrow$ Tigrinya, plus English pairs!

### Execution Command:
```powershell
$env:PYTHONUTF8=1; python scripts/train_nllb_lora.py `
  --batch_size 16 `
  --grad_accum 2 `
  --num_epochs 3 `
  --learning_rate 2e-4 `
  --merge_and_export `
  --eval_benchmarks
```

*(For 8GB GPUs, set `--batch_size 8 --grad_accum 4`)*

### What This Automated Script Does:
1. Loads `facebook/nllb-200-distilled-600M` in 4-bit QLoRA mode.
2. Injects trainable LoRA adapters on `q_proj`, `v_proj`, `k_proj`, `out_proj` (reducing trainable parameters from 600M to ~12M).
3. Trains over `train.jsonl` with early evaluation on `val.jsonl`.
4. Saves PEFT LoRA adapter weights to `models_optimized/nllb_lora_adapter/`.
5. **Automatically merges** the LoRA weights back into the full base NLLB architecture and saves to `models_optimized/nllb_merged/`.
6. **Automatically converts and quantizes** the merged model to CTranslate2 INT8 in `models_optimized/nllb_int8/`.
7. Tests sample translations across Amharic, Oromo, Tigrinya, and Somali to verify inference accuracy!
8. Runs HornMT benchmark evaluation to confirm BLEU score gains.

---

## 🎙️ Step 3: Speech-to-Text (STT) Training & Enhancement

### Goal:
Ensure reliable, low-latency speech recognition across all 5 languages without Whisper hallucination.

### The Multi-Engine Strategy:
1. **Amharic**: Native `snapwre/hohe-asr-amharic` (Dataset.ET Hohe Wav2Vec2-BERT, 16.1% WER).
2. **Afaan Oromo & Tigrinya**: `badrex/Ethio-ASR-multilingual-600M` coupled with dedicated lexicon-guided beam search decoders (`pyctcdecode` with `orm_unigrams.txt` and `tir_unigrams.txt` in `data/lexicon/`).
3. **English & Somali**: OpenAI Whisper (`openai/whisper-small` or fine-tuned Whisper).

### Option A: Prepare Real & Open Speech Datasets
```powershell
# Fetch Google FLEURS Amharic, Oromo, and Somali speech data
$env:PYTHONUTF8=1; python scripts/prepare_stt_data.py --source fleurs --max_samples_per_lang 500

# Or index local test WAV files
$env:PYTHONUTF8=1; python scripts/prepare_stt_data.py --source local
```

### Option B: Fine-Tune Whisper with LoRA
```powershell
$env:PYTHONUTF8=1; python scripts/train_whisper_lora.py `
  --base_model openai/whisper-small `
  --batch_size 8 `
  --grad_accum 4 `
  --num_epochs 3 `
  --merge_and_save
```

*(For 8GB GPUs, set `--base_model openai/whisper-base --batch_size 4 --grad_accum 8`)*

### Option C: Benchmark STT Latency & Word Error Rate (WER)
```powershell
$env:PYTHONUTF8=1; python scripts/evaluate_stt.py
```
This tests real audio samples (`hello_en.wav`, `hospital_en.wav`, `test_speech.wav`, `real_test1.wav`, `test_oromo_tts.wav`) and outputs WER and latency scores.

---

## 🔊 Step 4: Text-to-Speech (TTS) Verification & Benchmarking

### Goal:
Ensure crystal-clear, offline neural speech synthesis across all 5 languages with sub-second latency.

### Speech Models in Use:
- **Amharic**: `facebook/mms-tts-amh`
- **Afaan Oromo**: `facebook/mms-tts-orm` (or `mms-tts-gaz`)
- **Tigrinya**: `facebook/mms-tts-tir`
- **Somali**: `facebook/mms-tts-som`
- **English**: `facebook/mms-tts-eng` / `piper-tts`

### Run TTS Benchmark Suite:
```powershell
$env:PYTHONUTF8=1; python scripts/benchmark_tts.py
```

### Expected Output:
- Synthesizes speech for all 5 languages.
- Measures **RTF (Real-Time Factor)**: Should be $< 1.0\times$ (faster than real-time).
- Saves verified WAV files to `output_tts/test_amh.wav`, `output_tts/test_orm.wav`, etc.

---

## 🚀 Step 5: Full Automated Orchestrator

If you want to run the entire pipeline end-to-end with a single command:

```powershell
$env:PYTHONUTF8=1; python scripts/run_all_training.py --all
```

Or run individual phases:
```powershell
# Only Translation NMT training & CTranslate2 export:
$env:PYTHONUTF8=1; python scripts/run_all_training.py --nmt

# Only STT evaluation:
$env:PYTHONUTF8=1; python scripts/run_all_training.py --stt-eval

# Only TTS benchmarking:
$env:PYTHONUTF8=1; python scripts/run_all_training.py --tts-eval
```

---

## 🧪 Step 6: End-to-End System Validation

Once training and exports are done, verify the entire system:

### 1. Run Live Smart Pipeline Tests:
```powershell
$env:PYTHONUTF8=1; python test_smart_pipeline.py
$env:PYTHONUTF8=1; python test_oromo_end_to_end.py
$env:PYTHONUTF8=1; python test_scenario_clinic.py
$env:PYTHONUTF8=1; python test_scenario_market.py
```

### 2. Start the Backend Server:
```powershell
$env:PYTHONUTF8=1; python server.py
# Server will listen on http://0.0.0.0:8000
```

### 3. Test REST API:
```powershell
# Health check
curl http://127.0.0.1:8000/health

# Text translation
curl -X POST "http://127.0.0.1:8000/translate/text?text=Where%20is%20the%20hospital&src_lang=eng&tgt_lang=amh"
```

---

## 📱 Step 7: Packaging Artifacts for Flutter Mobile App

When ready to test or package for mobile:
1. The CTranslate2 INT8 model is located at: `models_optimized/nllb_int8/`
2. Translation Memory SQLite is located at: `data/translation_memory.db`
3. Lexicon unigrams are located at: `data/lexicon/`
4. If testing the Flutter app against the PC backend on the local Wi-Fi:
   ```bash
   cd ethiopian_translator
   flutter pub get
   flutter run
   ```

---

## 🛠️ Common Pitfalls & Troubleshooting Playbook

### 1. `bitsandbytes` CUDA Error on Windows:
```
RuntimeError: bitsandbytes was compiled without GPU support
```
**Fix**: Install official `bitsandbytes>=0.43.0` which has native Windows CUDA binaries:
```powershell
pip install --upgrade "bitsandbytes>=0.43.0"
```

### 2. CUDA Out of Memory (OOM):
```
torch.cuda.OutOfMemoryError: CUDA out of memory.
```
**Fix**:
1. Reduce `--batch_size` (e.g. from 16 to 8 or 4).
2. Increase `--grad_accum` (e.g. from 2 to 4 or 8) so the effective batch size stays identical.
3. Verify `--use_4bit` is enabled.
4. Reduce `--max_length` from 128 to 96.

### 3. UnicodeEncodeError: 'charmap' codec can't encode characters:
**Fix**: Windows default code page is CP1252. Always set:
```powershell
$env:PYTHONUTF8 = "1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### 4. PyTorch Installed with CPU Only:
**Fix**: Reinstall with CUDA 12.1 index:
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
```

### 5. Hugging Face Download Timeouts:
Set Hugging Face endpoint and timeout:
```powershell
$env:HF_HUB_ENABLE_HF_TRANSFER = "1"
pip install hf-transfer
```
