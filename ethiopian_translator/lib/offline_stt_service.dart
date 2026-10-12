import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';
import 'package:path_provider/path_provider.dart';
import 'offline_ort_config.dart';

/// Ultra-compact, low-memory on-device Speech-To-Text (ASR) service for Ethiopian languages.
/// Uses AfriHuBERT-UF INT8 quantized CTC acoustic model (117 MB on flash, < 40 MB working RAM).
class OfflineSttService {
  static const _modelAsset = 'assets/models/ethio_stt/model_quantized.onnx';
  static const _vocabAsset = 'assets/models/ethio_stt/vocab.json';
  static const _sampleRate = 16000;
  static const _padTokenId = 408;

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
      intraOpThreads: 2,
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
      final maxId = vocab.values.cast<int>().reduce(math.max);
      _vocabulary = List<String>.filled(maxId + 1, '');
      for (final entry in vocab.entries) {
        _vocabulary![entry.value as int] = entry.key;
      }
    }
  }

  Future<String> transcribe(String wavPath) async {
    try {
      await initialize();
      final wavFile = File(wavPath);
      if (!await wavFile.exists()) {
        debugPrint('[Offline STT] Audio file does not exist: $wavPath');
        return '';
      }
      final bytes = await wavFile.readAsBytes();
      final rawSamples = readWavPcm16(bytes);
      if (rawSamples.isEmpty) {
        debugPrint('[Offline STT] Audio samples are empty');
        return '';
      }

      // Zero-mean unit-variance normalization
      var mean = 0.0;
      for (final s in rawSamples) {
        mean += s;
      }
      mean /= rawSamples.length;

      var varSum = 0.0;
      for (final s in rawSamples) {
        final diff = s - mean;
        varSum += diff * diff;
      }
      final std = math.sqrt(varSum / rawSamples.length + 1e-7);

      final normalized = Float32List(rawSamples.length);
      for (var i = 0; i < rawSamples.length; i++) {
        normalized[i] = (rawSamples[i] - mean) / std;
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

      if (outputs.isEmpty) return '';
      final logits = outputs.first?.value;
      for (final output in outputs) {
        output?.release();
      }
      if (logits is! List) return '';
      final decoded = _decodeGreedy(logits);
      debugPrint('[Offline STT Decoded] "$decoded"');
      // Sequential Governor: Release native C++ session immediately to restore memory baseline
      dispose();
      return decoded;
    } catch (e, st) {
      debugPrint('[Offline STT Error] $e\n$st');
      dispose();
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

  String _decodeGreedy(dynamic rawLogits) {
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
          if (!token.startsWith('[') && token != '<s>' && token != '</s>') {
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
