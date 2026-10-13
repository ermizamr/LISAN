import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';
import 'package:path_provider/path_provider.dart';

import 'offline_ort_config.dart';
import 'offline_vits_tokenizer.dart';

/// Production On-Device Generative TTS Engine for Meta MMS-TTS VITS models.
///
/// Features:
/// 1. Sequential Governor: Allocates OrtSession on-demand and immediately purges
///    native pages via libc mallopt(M_PURGE) to guarantee <= 350 MB PSS limit.
/// 2. Zero-dependency 16-bit PCM WAV audio synthesizer at 16,000 Hz mono.
/// 3. Supports all 5 production languages: 'amh', 'orm', 'tir', 'som', 'eng'.
class OfflineVitsTts {
  static final OfflineVitsTts _instance = OfflineVitsTts._internal();
  factory OfflineVitsTts() => _instance;
  OfflineVitsTts._internal();

  final OfflineVitsTokenizer _tokenizer = OfflineVitsTokenizer();

  /// Map of language code to candidate file paths on disk.
  static const Map<String, List<String>> _modelPaths = {
    'amh': [
      '/sdcard/lisan_models/mms_tts/amh/model_quantized.onnx',
      '/sdcard/lisan_models/mms_tts/amh/model.onnx',
    ],
    'orm': [
      '/sdcard/lisan_models/mms_tts/orm/model_quantized.onnx',
      '/sdcard/lisan_models/mms_tts/orm/model.onnx',
    ],
    'tir': [
      '/sdcard/lisan_models/mms_tts/tir/model_quantized.onnx',
      '/sdcard/lisan_models/mms_tts/tir/model.onnx',
    ],
    'som': [
      '/sdcard/lisan_models/mms_tts/som/model_quantized.onnx',
      '/sdcard/lisan_models/mms_tts/som/model.onnx',
    ],
    'eng': [
      '/sdcard/lisan_models/mms_tts/eng/model_quantized.onnx',
      '/sdcard/lisan_models/mms_tts/eng/model.onnx',
    ],
  };

  /// Initialize tokenizer and ensure environment readiness.
  Future<void> initialize() async {
    await _tokenizer.initialize();
  }

  /// Check whether an ONNX model file exists for [lang].
  Future<File?> getModelFile(String lang) async {
    // 1. Check external candidate paths
    final candidates = _modelPaths[lang] ?? [];
    for (final path in candidates) {
      final f = File(path);
      if (await f.exists()) {
        return f;
      }
    }

    // 2. Check app support directory
    try {
      final dir = await getApplicationSupportDirectory();
      final appFile = File('${dir.path}/mms_tts_${lang}_quantized.onnx');
      if (await appFile.exists()) {
        return appFile;
      }

      // 3. Fallback: try loading from assets if bundled
      final assetPath = 'assets/models/mms_tts/$lang/model_quantized.onnx';
      try {
        final byteData = await rootBundle.load(assetPath);
        await appFile.writeAsBytes(byteData.buffer.asUint8List(), flush: true);
        debugPrint('[OfflineVitsTts] Extracted $lang TTS asset to ${appFile.path}');
        return appFile;
      } catch (_) {
        // Asset not packaged directly
      }
    } catch (e) {
      debugPrint('[OfflineVitsTts] Storage lookup error: $e');
    }

    return null;
  }

  /// Synthesize speech for [text] in [lang] directly on device.
  ///
  /// Returns a [File] pointing to a 16 kHz Mono PCM WAV audio file, or null if failed.
  Future<File?> synthesize(String text, String lang) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return null;

    final swTotal = Stopwatch()..start();

    // Ensure tokenizer is loaded
    if (!_tokenizer.isInitialized) {
      await initialize();
    }

    // Locate ONNX model
    final modelFile = await getModelFile(lang);
    if (modelFile == null) {
      debugPrint('[OfflineVitsTts] No model found on disk for language: $lang');
      return null;
    }

    // 1. Tokenize input text into interleaved token IDs
    final tokenIds = _tokenizer.encode(trimmed, lang);
    if (tokenIds.length <= 2) {
      debugPrint('[OfflineVitsTts] Empty or unrecognized token sequence for "$trimmed"');
      return null;
    }

    final seqLen = tokenIds.length;
    final inputIdsTensor = OrtValueTensor.createTensorWithDataList(
      Int64List.fromList(tokenIds),
      [1, seqLen],
    );
    final attentionMaskTensor = OrtValueTensor.createTensorWithDataList(
      Int64List.fromList(List.filled(seqLen, 1)),
      [1, seqLen],
    );

    OrtSession? session;
    final options = OfflineOrtConfig.createOptions(
      intraOpThreads: 2,
      interOpThreads: 1,
    );
    final runOptions = OrtRunOptions();
    dynamic rawWaveform;

    try {
      final swInf = Stopwatch()..start();
      debugPrint('[OfflineVitsTts] [Governor] Allocating VITS session for $lang (${tokenIds.length} tokens)...');
      session = OrtSession.fromFile(modelFile, options);

      final outputs = session.run(runOptions, {
        'input_ids': inputIdsTensor,
        'attention_mask': attentionMaskTensor,
      });

      swInf.stop();
      debugPrint('[OfflineVitsTts] Inference completed in ${swInf.elapsedMilliseconds} ms');

      if (outputs.isNotEmpty) {
        rawWaveform = outputs.first?.value;
      }

      for (final out in outputs) {
        out?.release();
      }
    } catch (e, st) {
      debugPrint('[OfflineVitsTts] Synthesis error: $e\n$st');
      return null;
    } finally {
      // SEQUENTIAL GOVERNOR: Instantly release OrtSession and run options
      runOptions.release();
      options.release();
      session?.release();
      session = null;
      inputIdsTensor.release();
      attentionMaskTensor.release();

      // Return dirty heap pages directly to the Linux kernel
      OfflineOrtConfig.trimNativeMemory();
      debugPrint('[OfflineVitsTts] [Governor] Session released & native heap trimmed ✓');
    }

    if (rawWaveform == null) {
      debugPrint('[OfflineVitsTts] Waveform output was null');
      return null;
    }

    // Extract float audio samples
    final samples = _extractAudioSamples(rawWaveform);
    if (samples.isEmpty) {
      debugPrint('[OfflineVitsTts] Waveform contained 0 samples');
      return null;
    }

    // Convert samples to 16 kHz Mono PCM WAV bytes
    final wavBytes = _pcmToWavBytes(samples, sampleRate: 16000);

    // Write to a temporary file
    final tempDir = await getTemporaryDirectory();
    final outPath = '${tempDir.path}/lisan_vits_${lang}_${DateTime.now().millisecondsSinceEpoch}.wav';
    final outFile = File(outPath);
    await outFile.writeAsBytes(wavBytes, flush: true);

    swTotal.stop();
    final durationSec = samples.length / 16000.0;
    debugPrint(
      '[OfflineVitsTts] Generated ${durationSec.toStringAsFixed(2)}s audio '
      '(${samples.length} samples, ${wavBytes.length} bytes) in ${swTotal.elapsedMilliseconds} ms. Saved to: $outPath',
    );

    return outFile;
  }

  /// Extracts flat list of doubles from ONNX Runtime output tensor.
  static List<double> _extractAudioSamples(dynamic rawOutput) {
    final samples = <double>[];
    if (rawOutput is List) {
      if (rawOutput.isNotEmpty && rawOutput.first is List) {
        for (final item in rawOutput.first as List) {
          if (item is num) {
            samples.add(item.toDouble());
          }
        }
      } else {
        for (final item in rawOutput) {
          if (item is num) {
            samples.add(item.toDouble());
          }
        }
      }
    }
    return samples;
  }

  /// Encodes normalized float samples [-1.0, 1.0] into a standard 16-bit PCM WAV file.
  static Uint8List _pcmToWavBytes(List<double> samples, {int sampleRate = 16000}) {
    final numSamples = samples.length;
    final subChunk2Size = numSamples * 2; // 2 bytes per 16-bit sample
    final chunkSize = 36 + subChunk2Size;
    final byteRate = sampleRate * 1 * 2; // sampleRate * channels * bytesPerSample

    final buffer = ByteData(44 + subChunk2Size);

    // RIFF chunk descriptor
    buffer.setUint8(0, 0x52); // 'R'
    buffer.setUint8(1, 0x49); // 'I'
    buffer.setUint8(2, 0x46); // 'F'
    buffer.setUint8(3, 0x46); // 'F'
    buffer.setUint32(4, chunkSize, Endian.little);
    buffer.setUint8(8, 0x57);  // 'W'
    buffer.setUint8(9, 0x41);  // 'A'
    buffer.setUint8(10, 0x56); // 'V'
    buffer.setUint8(11, 0x45); // 'E'

    // fmt sub-chunk
    buffer.setUint8(12, 0x66); // 'f'
    buffer.setUint8(13, 0x6D); // 'm'
    buffer.setUint8(14, 0x74); // 't'
    buffer.setUint8(15, 0x20); // ' '
    buffer.setUint32(16, 16, Endian.little); // Subchunk1Size = 16
    buffer.setUint16(20, 1, Endian.little);  // AudioFormat = 1 (PCM)
    buffer.setUint16(22, 1, Endian.little);  // NumChannels = 1 (Mono)
    buffer.setUint32(24, sampleRate, Endian.little);
    buffer.setUint32(28, byteRate, Endian.little);
    buffer.setUint16(32, 2, Endian.little);  // BlockAlign = 2
    buffer.setUint16(34, 16, Endian.little); // BitsPerSample = 16

    // data sub-chunk
    buffer.setUint8(36, 0x64); // 'd'
    buffer.setUint8(37, 0x61); // 'a'
    buffer.setUint8(38, 0x74); // 't'
    buffer.setUint8(39, 0x61); // 'a'
    buffer.setUint32(40, subChunk2Size, Endian.little);

    // Write PCM 16-bit samples
    var offset = 44;
    for (var i = 0; i < numSamples; i++) {
      final clamped = samples[i].clamp(-1.0, 1.0);
      final pcmSample = (clamped * 32767.0).round().toInt();
      buffer.setInt16(offset, pcmSample, Endian.little);
      offset += 2;
    }

    return buffer.buffer.asUint8List();
  }
}
