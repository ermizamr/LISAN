# On-Device Inference Architecture — Lisan App
## How AI Runs Directly on Android (No Server)

---

## Overview

```
┌─────────────────────────────────────────────────────┐
│                  ANDROID PHONE                      │
│                                                     │
│  ┌──────────┐   ┌──────────────┐   ┌────────────┐  │
│  │  Flutter │──▶│ONNX Runtime  │──▶│  Android   │  │
│  │   UI     │   │  (native)    │   │    TTS     │  │
│  └──────────┘   └──────────────┘   └────────────┘  │
│                       │                            │
│              ┌─────────┴──────────┐               │
│              │   onnx_models/     │               │
│              │  ethio_stt.onnx    │ ~150MB        │
│              │  nllb_encoder.onnx │ ~150MB        │
│              │  nllb_decoder.onnx │ ~300MB        │
│              │  whisper_tiny.onnx │  ~40MB        │
│              └────────────────────┘               │
│                  Total: ~640MB INT8               │
└─────────────────────────────────────────────────────┘
```

## Steps to Go Fully On-Device

### Step 1 — Export models to ONNX INT8 (PC, run once)
```bash
python ai_pipeline/export_onnx.py all
# Outputs: onnx_models/ (~640MB total)
```

### Step 2 — Add ONNX Runtime to Flutter
```yaml
# pubspec.yaml
dependencies:
  onnxruntime: ^1.2.0          # Flutter ONNX Runtime plugin
  flutter_sound: ^9.2.13       # Microphone recording
  permission_handler: ^11.0.0  # Mic permission
```

### Step 3 — Copy models to Android assets
```
ethiopian_translator/
  assets/
    models/
      ethio_stt.onnx       ← Amharic+Oromo+Tigrinya STT
      nllb_encoder.onnx    ← Translation encoder
      nllb_decoder.onnx    ← Translation decoder (merged)
      whisper_tiny.onnx    ← English+Somali STT
      tokenizer/           ← JSON vocab files (small)
```

### Step 4 — Flutter ONNX inference layer
```dart
// lib/services/on_device_translator.dart
import 'package:onnxruntime/onnxruntime.dart';

class OnDeviceTranslator {
  late OrtSession _sttSession;
  late OrtSession _encoderSession;
  late OrtSession _decoderSession;

  Future<void> loadModels() async {
    final sessionOptions = OrtSessionOptions()
      ..setIntraOpNumThreads(2)  // Use 2 CPU cores
      ..setInterOpNumThreads(1);

    _sttSession = await OrtSession.fromAsset(
      'assets/models/ethio_stt.onnx',
      sessionOptions,
    );
    _encoderSession = await OrtSession.fromAsset(
      'assets/models/nllb_encoder.onnx',
      sessionOptions,
    );
    _decoderSession = await OrtSession.fromAsset(
      'assets/models/nllb_decoder.onnx',
      sessionOptions,
    );
  }

  Future<String> transcribe(Float32List audioData, String lang) async {
    final inputs = {'input_values': OrtValueTensor.createTensorWithDataList(
      audioData, [1, audioData.length]
    )};
    final outputs = await _sttSession.runAsync(null, inputs);
    // Decode CTC output to text
    return _ctcDecode(outputs[0]!.value as List<List<double>>);
  }

  Future<String> translate(String text, String srcLang, String tgtLang) async {
    // Tokenize → encode → decode → detokenize
    final tokens = _tokenize(text, srcLang);
    final encoded = await _encode(tokens);
    final decoded = await _decode(encoded, tgtLang);
    return _detokenize(decoded);
  }
}
```

### Step 5 — Android TTS for Amharic output
```dart
// lib/services/tts_service.dart
import 'package:flutter_tts/flutter_tts.dart';

class TTSService {
  final FlutterTts _tts = FlutterTts();

  Future<void> speak(String text, String langCode) async {
    // Android 12+ supports Amharic TTS natively
    final locale = {
      'amh': 'am-ET',
      'eng': 'en-US',
      'orm': 'om-ET',
      'som': 'so-SO',
      'tir': 'ti-ET',
    }[langCode] ?? 'en-US';

    await _tts.setLanguage(locale);
    await _tts.speak(text);
  }
}
```

---

## Expected Performance on Android

| Operation | Time (PyTorch PC) | Time (ONNX INT8 Phone) |
|-----------|-------------------|------------------------|
| STT (5s audio) | ~2s | ~3-5s |
| Translation | ~0.8s | ~1-2s |
| TTS | ~0.2s | ~0.1s (native) |
| **Total** | **~3s** | **~5-8s** |

> These are estimates for a mid-range phone (Snapdragon 680 / Helio G85).
> High-end phones (Snapdragon 8 Gen) will be 2-3x faster.

---

## Current Status

| Task | Status |
|------|--------|
| Export NLLB-200 → ONNX INT8 | ⬇️ Running now |
| Export EthioSTT → ONNX INT8 | ⏳ Next |
| Add onnxruntime Flutter plugin | ⏳ Pending |
| Copy models to Android assets | ⏳ Pending |
| Wire inference in Flutter | ⏳ Pending |

---

## Offline Story for Hackathon Pitch

> **"Lisan works completely offline. The AI models run directly on your phone.
> No internet, no server, no data leaving your device. Works even in rural
> areas with no connectivity."**

This is the key differentiator from Google Translate and other apps.
