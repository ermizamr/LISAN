import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';
import 'package:path_provider/path_provider.dart';
import 'offline_ort_config.dart';

class SttResult {
  final String text;
  final String? detectedLanguage;
  final int durationMs;

  const SttResult({
    required this.text,
    this.detectedLanguage,
    this.durationMs = 0,
  });

  @override
  String toString() =>
      'SttResult(text: "$text", lang: $detectedLanguage, duration: ${durationMs}ms)';
}

/// Ultra-compact, low-memory on-device Speech-To-Text (ASR) service for Ethiopian languages.
/// Uses AfriHuBERT-UF INT8 quantized CTC acoustic model (117 MB on flash, < 40 MB working RAM).
class OfflineSttService {
  static const _modelAsset = 'assets/models/ethio_stt/model_quantized.onnx';
  static const _vocabAsset = 'assets/models/ethio_stt/vocab.json';
  static const _sampleRate = 16000;
  int _padTokenId = 408;

  OrtSession? _session;
  List<String>? _vocabulary;

  Future<void> initialize() async {
    if (_session != null && _vocabulary != null) return;

    // Check external directory first (/sdcard/lisan_models/ethio_stt/)
    final externalModel =
        File('/sdcard/lisan_models/ethio_stt/model_quantized.onnx');
    File modelFile;
    if (await externalModel.exists()) {
      modelFile = externalModel;
      debugPrint('[Offline STT] Loading model from ${modelFile.path}');
    } else {
      final directory = await getApplicationSupportDirectory();
      modelFile = File('${directory.path}/ethio_stt_model_quantized.onnx');
      if (!await modelFile.exists()) {
        try {
          final modelBytes = await rootBundle.load(_modelAsset);
          await modelFile.writeAsBytes(
            modelBytes.buffer.asUint8List(),
            flush: true,
          );
        } catch (e) {
          debugPrint('[Offline STT] Model file not found in assets: $e');
        }
      }
    }

    if (!await modelFile.exists()) {
      throw StateError('STT model not found at ${modelFile.path} or on /sdcard');
    }

    final options = OfflineOrtConfig.createOptions(
      intraOpThreads: 4,
      interOpThreads: 1,
    );
    try {
      _session = OrtSession.fromFile(modelFile, options);
    } finally {
      options.release();
    }

    // 1. Vocabulary
    if (_vocabulary == null) {
      String vocabJson;
      final externalVocab = File('/sdcard/lisan_models/ethio_stt/vocab.json');
      if (await externalVocab.exists()) {
        vocabJson = await externalVocab.readAsString();
      } else {
        vocabJson = await rootBundle.loadString(_vocabAsset);
      }
      final vocab = (jsonDecode(vocabJson) as Map<String, dynamic>);
      _padTokenId = (vocab['[PAD]'] ??
              vocab['<pad>'] ??
              vocab['<blank>'] ??
              vocab['[pad]'] ??
              408) as int;
      final maxId = vocab.values.cast<int>().reduce(math.max);
      _vocabulary = List<String>.filled(maxId + 1, '');
      for (final entry in vocab.entries) {
        _vocabulary![entry.value as int] = entry.key;
      }
    }
  }

  /// Trims leading and trailing ambient silence using frame RMS energy and adaptive thresholding.
  /// Preserves 150ms lead-in padding and 200ms trailing padding to prevent cutting initial plosives or final vowel decay.
  static List<double> trimSilence(List<double> samples, {int sampleRate = _sampleRate}) {
    if (samples.isEmpty) return samples;

    final frameSize = (sampleRate * 0.02).round(); // 20ms frames (320 samples at 16kHz)
    if (samples.length < frameSize * 3) return samples;

    final numFrames = samples.length ~/ frameSize;
    final frameEnergies = Float32List(numFrames);

    var maxEnergy = 0.0;
    var sumEnergy = 0.0;

    for (var f = 0; f < numFrames; f++) {
      final start = f * frameSize;
      var sumSq = 0.0;
      for (var i = 0; i < frameSize; i++) {
        final s = samples[start + i];
        sumSq += s * s;
      }
      final rms = math.sqrt(sumSq / frameSize);
      frameEnergies[f] = rms;
      sumEnergy += rms;
      if (rms > maxEnergy) maxEnergy = rms;
    }

    // If whole clip is quieter than 0.015 RMS (whisper or near total silence), keep as is
    if (maxEnergy < 0.015) {
      return samples;
    }

    final avgEnergy = sumEnergy / numFrames;
    // Dynamic speech threshold: at least 0.012, or 18% of max energy, or 0.6 of average
    final speechThreshold = math.max(0.012, math.min(maxEnergy * 0.18, avgEnergy * 0.6));

    var firstVoiceFrame = -1;
    for (var f = 0; f < numFrames; f++) {
      if (frameEnergies[f] >= speechThreshold) {
        firstVoiceFrame = f;
        break;
      }
    }

    var lastVoiceFrame = -1;
    for (var f = numFrames - 1; f >= 0; f--) {
      if (frameEnergies[f] >= speechThreshold) {
        lastVoiceFrame = f;
        break;
      }
    }

    if (firstVoiceFrame == -1 || lastVoiceFrame == -1 || firstVoiceFrame > lastVoiceFrame) {
      return samples;
    }

    // Add padding margins: 150ms before, 200ms after
    final leadMarginFrames = (sampleRate * 0.15 / frameSize).round();
    final tailMarginFrames = (sampleRate * 0.20 / frameSize).round();

    final startFrame = math.max(0, firstVoiceFrame - leadMarginFrames);
    final endFrame = math.min(numFrames - 1, lastVoiceFrame + tailMarginFrames);

    final startSample = startFrame * frameSize;
    final endSample = math.min(samples.length, (endFrame + 1) * frameSize);

    return samples.sublist(startSample, endSample);
  }

  Future<String> transcribe(String wavPath) async {
    final result = await transcribeDetailed(wavPath);
    return result.text;
  }

  Future<SttResult> transcribeDetailed(String wavPath) async {
    final sw = Stopwatch()..start();
    try {
      await initialize();
      final wavFile = File(wavPath);
      if (!await wavFile.exists()) {
        debugPrint('[Offline STT] Audio file does not exist: $wavPath');
        return const SttResult(text: '');
      }
      final bytes = await wavFile.readAsBytes();
      final rawSamples = readWavPcm16(bytes);
      if (rawSamples.isEmpty) {
        debugPrint('[Offline STT] Audio samples are empty');
        return const SttResult(text: '');
      }

      // Energy-based VAD: Trim leading and trailing ambient silence
      final trimmedSamples = trimSilence(rawSamples);
      debugPrint(
        '[Offline STT] VAD trimmed: ${rawSamples.length} -> ${trimmedSamples.length} samples (${(trimmedSamples.length / _sampleRate).toStringAsFixed(2)}s)',
      );

      // Zero-mean unit-variance normalization on active speech
      var mean = 0.0;
      for (final s in trimmedSamples) {
        mean += s;
      }
      mean /= trimmedSamples.length;

      var varSum = 0.0;
      for (final s in trimmedSamples) {
        final diff = s - mean;
        varSum += diff * diff;
      }
      final std = math.sqrt(varSum / trimmedSamples.length + 1e-7);

      final normalized = Float32List(trimmedSamples.length);
      for (var i = 0; i < trimmedSamples.length; i++) {
        normalized[i] = (trimmedSamples[i] - mean) / std;
      }

      final tensor = OrtValueTensor.createTensorWithDataList(
        normalized,
        [
          1,
          normalized.length,
        ],
      );
      final runOptions = OrtRunOptions();
      List<OrtValue?>? outputs;
      try {
        outputs = _session!.run(runOptions, {
          'input_values': tensor,
        });
      } finally {
        runOptions.release();
        tensor.release();
      }

      if (outputs.isEmpty) return const SttResult(text: '');
      final logits = outputs.first?.value;
      for (final output in outputs) {
        output?.release();
      }
      if (logits is! List) return const SttResult(text: '');

      final detectedLangs = <String>[];
      final decoded = _decodeGreedy(logits, detectedLangs);
      sw.stop();
      debugPrint('[Offline STT Decoded] "$decoded" (${sw.elapsedMilliseconds}ms, langs: $detectedLangs)');

      String? langToken;
      if (detectedLangs.isNotEmpty) {
        final first = detectedLangs.first.toLowerCase();
        if (first.contains('amh')) {
          langToken = 'amh';
        } else if (first.contains('orm')) {
          langToken = 'orm';
        } else if (first.contains('tir')) {
          langToken = 'tir';
        } else if (first.contains('sid')) {
          langToken = 'sid';
        } else if (first.contains('wal')) {
          langToken = 'wal';
        }
      }

      // Trim dirty native memory pages without destroying the warm ORT session
      OfflineOrtConfig.trimNativeMemory();
      return SttResult(
        text: decoded,
        detectedLanguage: langToken,
        durationMs: sw.elapsedMilliseconds,
      );
    } catch (e, st) {
      debugPrint('[Offline STT Error] $e\n$st');
      rethrow;
    }
  }

  /// Parses standard 16-bit PCM WAV bytes and returns normalized audio samples in [-1.0, 1.0].
  static List<double> readWavPcm16(Uint8List bytes) {
    if (bytes.length < 44 ||
        _ascii(bytes, 0, 4) != 'RIFF' ||
        _ascii(bytes, 8, 4) != 'WAVE') {
      throw const FormatException('Expected a PCM WAV file');
    }

    var offset = 12;
    var channels = 1;
    var sampleRate = _u32(bytes, 24);
    var bitsPerSample = 16;
    var dataStart = -1;
    var dataLength = 0;
    while (offset + 8 <= bytes.length) {
      final chunkId = _ascii(bytes, offset, 4);
      final chunkLength = _u32(bytes, offset + 4);
      final chunkStart = offset + 8;
      if (chunkId == 'fmt ' && chunkLength >= 16) {
        channels = _u16(bytes, chunkStart + 2);
        sampleRate = _u32(bytes, chunkStart + 4);
        bitsPerSample = _u16(bytes, chunkStart + 14);
      } else if (chunkId == 'data') {
        dataStart = chunkStart;
        dataLength = math.min(chunkLength, bytes.length - chunkStart);
        break;
      }
      offset = chunkStart + chunkLength + (chunkLength.isOdd ? 1 : 0);
    }

    if (dataStart < 0 || bitsPerSample != 16 || sampleRate != _sampleRate) {
      throw FormatException('Expected 16-bit ${_sampleRate}Hz PCM WAV');
    }
    final frameBytes = channels * 2;
    final sampleCount = dataLength ~/ frameBytes;
    final samples = List<double>.filled(sampleCount, 0.0);
    for (var index = 0; index < sampleCount; index++) {
      var sum = 0.0;
      for (var channel = 0; channel < channels; channel++) {
        final position = dataStart + (index * frameBytes) + (channel * 2);
        sum += _i16(bytes, position);
      }
      // 16-bit PCM amplitude normalized to [-1.0, 1.0]
      samples[index] = (sum / channels) / 32768.0;
    }
    return samples;
  }

  String _decodeGreedy(dynamic rawLogits, [List<String>? detectedLangsOut]) {
    final vocabulary = _vocabulary!;
    final sequence = rawLogits is List && rawLogits.isNotEmpty
        ? rawLogits[0] as List
        : const [];
    var previous = -1;
    final output = StringBuffer();

    for (final frame in sequence) {
      if (frame is! List || frame.isEmpty) continue;
      var best = 0;
      for (var index = 1; index < frame.length; index++) {
        if ((frame[index] as num) > (frame[best] as num)) best = index;
      }
      if (best != _padTokenId) {
        if (best != previous && best < vocabulary.length) {
          final token = vocabulary[best];
          if (token.startsWith('[') && token.endsWith(']')) {
            detectedLangsOut?.add(token);
          } else if (token != '<s>' && token != '</s>') {
            output.write(token == '|' ? ' ' : token);
          }
        }
      }
      previous = best;
    }
    return output.toString().replaceAll(RegExp(r'\s+'), ' ').trim();
  }

  static String _ascii(Uint8List bytes, int start, int length) =>
      String.fromCharCodes(bytes.sublist(start, start + length));

  static int _u16(Uint8List bytes, int offset) =>
      bytes[offset] | (bytes[offset + 1] << 8);

  static int _u32(Uint8List bytes, int offset) =>
      bytes[offset] |
      (bytes[offset + 1] << 8) |
      (bytes[offset + 2] << 16) |
      (bytes[offset + 3] << 24);

  static int _i16(Uint8List bytes, int offset) {
    final value = _u16(bytes, offset);
    return value >= 0x8000 ? value - 0x10000 : value;
  }

  void dispose() {
    _session?.release();
    _session = null;
    OfflineOrtConfig.trimNativeMemory();
  }
}
