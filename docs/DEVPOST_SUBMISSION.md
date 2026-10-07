<p align="center">
  <img src="banners/lisan_hackathon_banner_dark.jpg" alt="LISAN (ልሳን) Banner" width="100%" />
</p>

# 🌍 LISAN (ልሳን) — Offline-First Voice AI for Ethiopian Languages

### *Speak freely. Be understood.*
> **Real-time, on-device speech-to-speech translation bridging Ethiopia and the Horn of Africa — trained on AWS SageMaker, running 100% offline at the edge with zero cloud dependency.**

---

## 💡 Inspiration

Ethiopia is a vibrant mosaic of over **120 million people** speaking more than **80 distinct languages**. Yet, this cultural richness often turns into an acute communication divide in everyday life:

* In **regional healthcare triage**, a doctor in an Amhara referral clinic may struggle to understand an emergency patient from the Oromia or Somali regions. In critical situations, seconds lost to language barriers carry life-altering consequences.
* In **rural agricultural markets**, grain, spice, and coffee traders travel between regional states where different mother tongues (Amharic, Afaan Oromoo, Tigrinya, Somali) intersect daily.
* In **disaster relief, transit hubs, and civic offices**, language access is fundamental to human dignity.

Every major translation app on the market today (Google Translate, cloud translation APIs) assumes a constant, high-speed 5G or broadband connection. But in rural Ethiopia and across the Horn of Africa, **network blackouts, remote cellular dead zones, and exorbitant mobile data costs** mean cloud tools fail exactly when and where they are needed most.

Furthermore, Ethiopian languages have long been relegated to "low-resource" status by global tech companies, plagued by poor tokenization, awkward literal syntax, and cultural misinterpretations.

We asked ourselves:  
*What if two people speaking completely different mother tongues could hold a single smartphone between them, press a single tactile button, and converse naturally in real-time — with 100% privacy, sub-6-second speed, and absolutely ZERO internet connection?*

That question gave birth to **LISAN (ልሳን)** — derived from the ancient Ge'ez root for *"tongue"*, *"language"*, and *"human speech"*.

---

## 📱 What It Does

**LISAN (ልሳን)** is a standalone, offline-capable mobile voice communicator. Two individuals who speak different languages hold a single phone and communicate through it seamlessly.

### Core Capabilities:
1. **100% Offline, On-Device AI**: Everything happens on the smartphone's local processor. No internet, no Wi-Fi, no cloud latency, no server subscriptions, and total data privacy.
2. **Conversational Speech-to-Speech**:
   * **Speaker A** speaks in their native tongue (e.g., Amharic: *"በአቅራቢያው ያለው ሆስፒታል የት ነው?"*).
   * **LISAN** captures, transcribes, translates, and vocalizes the translation in the partner's language (e.g., English: *"Where is the nearest hospital?"* or Afaan Oromoo: *"Hospitaalichi eessa jira?"*).
   * **Speaker B** taps the tactile microphone to reply, and Speaker A hears the response in their own language.
3. **Supported Languages**:
   * **Amharic (አማርኛ)** — Ethiopic Ge'ez script
   * **Afaan Oromoo** — Latin Qubee script
   * **Tigrinya (ትግርኛ)** — Ethiopic Ge'ez script
   * **Somali (Soomaali)** — Latin script
   * **English (EN)** — for tourists, aid workers, and global visitors
4. **Tactile Industrial Design System**: Inspired by classic industrial design (Dieter Rams / Teenage Engineering), the UI replaces complex menus with an intuitive physical centerpiece: a warm vermilion acoustic button surrounded by concentric resonance rings that pulsate with speech status.

---

## ⚙️ How We Built It: AWS Cloud Training to Edge Deployment

LISAN is engineered on a **hybrid AI architecture**: heavy distributed fine-tuning in the cloud using **Amazon Web Services (AWS)**, followed by aggressive model compression and INT8 quantization for deployment on **Flutter Mobile (Android/iOS)**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ☁️ AWS CLOUD TRAINING PIPELINE                         │
│                                                                             │
│  [ dataset.et / Snapwre ] ──> 68,000+ Curated Pairs (AM, OR, TI, SO, EN)     │
│                                          │                                  │
│                                          ▼                                  │
│  [ Amazon SageMaker Studio / EC2 GPU (g4dn.xlarge / NVIDIA T4 16GB) ]       │
│  • Meta NLLB-200 Distilled 600M Base Architecture                           │
│  • Hugging Face PEFT + BitsAndBytes 4-Bit QLoRA Fine-Tuning                 │
│  • SacreBLEU & Cross-Entropy Multi-Task Loss Convergence                    │
│                                          │                                  │
│                                          ▼                                  │
│  [ Model Export & Quantization ] ──> INT8 ONNX Engine (model_quantized.onnx)│
└─────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼ (Bundle into Mobile APK)
┌─────────────────────────────────────────────────────────────────────────────┐
│                    📱 100% OFFLINE ON-DEVICE EDGE RUNTIME                    │
│                                                                             │
│  [ 🎙️ Audio Capture ] ──> 16kHz In-Memory Streaming (No FFmpeg disk lag)    │
│                                          │                                  │
│  [ ⚡ Whisper Tiny STT ] ──> 0.41s Sub-Second Local Transcription           │
│                                          │                                  │
│  [ 🧠 NLLB-200 INT8 ONNX ] ──> 609MB Quantized Mobile Neural Translator      │
│     (Pre-warmed Engine + num_beams=2 inference optimization)                │
│                                          │                                  │
│  [ 🔊 Offline Synthesizer ] ──> Sub-0.25s Acoustic Vocalization              │
│                                          │                                  │
│  [ 🎨 Flutter Native UI ] ──> Tactile LisanTheme • 5.9s Roundtrip Experience│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Cloud Fine-Tuning with Amazon Web Services (AWS)
* **Amazon SageMaker Studio & Amazon EC2 (`g4dn.xlarge` / `g5.xlarge`)**:
  * We utilized AWS cloud GPU compute (NVIDIA Tesla T4 16GB VRAM and A10G 24GB VRAM) to fine-tune **Meta NLLB-200 Distilled 600M**.
  * Used **PyTorch 2.x GPU-optimized kernels**, **Hugging Face `peft`**, and **BitsAndBytes 4-bit QLoRA** to fine-tune across **64,623 training pairs** and **3,401 validation pairs** sourced from the open Ethiopian language corpus `dataset.et` (managed by NVIDIA Inception member Snapwre).
  * Reduced training VRAM consumption from ~18GB down to under 8GB, enabling rapid hyperparameter sweeps in ~2 hours per epoch.

### 2. Edge Compression & ONNX Quantization
* Merged LoRA adapters with the base model and converted the full sequence-to-sequence transformer into **ONNX format**.
* Applied **symmetric INT8 dynamic quantization** (`model_quantized.onnx`), shrinking the model footprint to **~609 MB** so it fits comfortably within the memory limits of budget smartphones.

### 3. Sub-Second Speech-to-Text (STT)
* Deployed **OpenAI Whisper Tiny** locally.
* Traditional Whisper pipelines invoke external FFmpeg subprocesses and disk file writes that introduce 1.5–2.0s of overhead. We re-engineered the pipeline to stream raw PCM audio from memory into a 16kHz float32 NumPy buffer via `soundfile`, slashing transcription latency to **0.41 seconds**.

### 4. Cross-Platform Mobile Client (Flutter)
* Built using **Flutter** with a custom C-interop bridge to the ONNX Runtime Mobile C-API.
* Designed a custom tactile design system (`LisanTheme`) with calibrated Ge'ez fidel font rendering, dynamic audio visualizers, and state-preserving conversation logs.

---

## 🧗 Challenges We Ran Into

1. **Sub-6s Edge Latency on Modest Hardware**:
   * *Problem*: In our first local benchmark, the translation transformer exhibited a 13-second "cold-start" delay on the first query, and beam search with `num_beams=4` was sluggish on CPU.
   * *Solution*: We implemented a background engine warm-up during app boot that initializes the KV-cache, and tuned beam search to `num_beams=2`. This slashed latency by 65% with zero perceptible loss in BLEU score, achieving a **~5.9s end-to-end roundtrip**.
2. **Linguistic Idiosyncrasies & Tokenizer Code Clashes**:
   * *Problem*: In Meta's NLLB-200 codebase, Afaan Oromoo is indexed as `gaz_Latn` (West Central Oromo) rather than the standard ISO code `orm_Latn`. Querying `orm_Latn` caused silent translation failures.
   * *Solution*: We built a strict language registry mapping system that normalizes BCP-47 codes to internal model dictionary tokens seamlessly.
3. **Encoding Hazards Across Scripts**:
   * Ethiopic Ge'ez characters (ሀ, ሁ, ሂ, ል, ሳ, ን) require careful handling on Windows and mobile memory buffers. We enforced strict UTF-8 stream handling throughout the audio and tokenizer pipelines to prevent character corruption.
4. **Offline Mobile Memory Footprint**:
   * Mobile operating systems will kill apps consuming over 1.2GB of RAM. By quantizing NLLB-200 to INT8 and keeping Whisper Tiny in memory-mapped pages, LISAN runs comfortably within an 800MB working set.

---

## 🏆 Accomplishments That We're Proud Of

* **Zero Cloud Latency, 100% Autonomy**: Proving that cutting-edge neural speech translation can run completely offline on a smartphone without compromising linguistic fluency.
* **0.41s Speech Recognition**: Achieving ultra-fast transcription on local audio input without heavy cloud server round-trips.
* **Bridging Low-Resource Languages**: Delivering reliable, idiomatic bidirectional translation between Amharic, Afaan Oromo, Tigrinya, Somali, and English.
* **Product-Grade Visual Identity**: Crafting a brand and interface that feels like a real consumer technology product—warm, tactile, respectful of local culture, and accessible to non-technical users.
* **Reproducible AWS Workflow**: Authoring a production-ready SageMaker notebook and EC2 training script that allows anyone in the Ethiopian AI community to reproduce or extend our fine-tuning results.

---

## 📚 What We Learned

* **QLoRA on AWS SageMaker is a Game Changer for Low-Resource NLP**: Fine-tuning billion-scale multilingual models no longer requires multi-million dollar GPU clusters. A university or community team with an AWS credit allocation can adapt foundation models to indigenous languages in hours.
* **The Importance of Audio IO in End-to-End Latency**: When optimizing edge AI, the bottle-neck is often not the neural network itself, but the disk operations, format conversions, and audio resampling around it.
* **Cross-Lingual Morphological Differences**: Moving between Semitic languages (Amharic, Tigrinya) with root-and-pattern morphology and Cushitic languages (Afaan Oromo, Somali) with agglutinative structures taught us deep respect for specialized tokenization.

---

## 🔮 What's Next for LISAN

* **AWS Bedrock & Batch Fine-Tuning Pipeline**: Setting up automated data ingestion from community contributors to continuously fine-tune checkpoints using AWS SageMaker Pipelines.
* **Expanding to Additional Regional Languages**: Integrating **Sidama**, **Wolaytta**, **Gurage**, and **Afar**.
* **Simultaneous Full-Duplex Translation**: Moving from push-to-talk to continuous ambient translation using streaming CTC decoders.
* **LISAN Hardware Edition**: Prototyping a dedicated, ultra-low-cost handheld translation device powered by an embedded NPU and solar charging for remote health workers and rural schools.

---

## 🧰 Built With

* **Cloud & Infrastructure**: AWS SageMaker Studio, Amazon EC2 (`g4dn.xlarge`), AWS Deep Learning AMIs
* **Deep Learning Frameworks**: PyTorch 2.x, Hugging Face Transformers, Hugging Face PEFT, BitsAndBytes
* **Foundation Models**: Meta NLLB-200 (Distilled 600M), OpenAI Whisper Tiny
* **Quantization & Edge Runtime**: ONNX Runtime Mobile, CTranslate2, INT8 Symmetric Quantization
* **Mobile & Frontend**: Flutter 3.24, Dart, Custom C-Interop Bindings
* **Audio Engineering**: Python SoundDevice, SciPy, NumPy, PyTTSx3, Miniaudio
* **Datasets**: dataset.et / Snapwre (NVIDIA Inception Member)

---

## 💻 Try It Out (Quick Start)

### 1. Run Text Translation Test
```powershell
$env:PYTHONUTF8=1; python ai_pipeline/test_translation.py
```

### 2. Run Full Speech-to-Text & End-to-End Pipeline
```powershell
$env:PYTHONUTF8=1; python ai_pipeline/test_stt.py
```

### 3. Launch Interactive Conversational CLI
```powershell
$env:PYTHONUTF8=1; python ai_pipeline/live_translate.py
```

### 4. Run Mobile App
```bash
cd ethiopian_translator
flutter run
```

---

<p align="center">
  <b>LISAN (ልሳን)</b> — <i>Breaking language barriers across Ethiopia and the Horn of Africa. Completely offline.</i>
</p>
