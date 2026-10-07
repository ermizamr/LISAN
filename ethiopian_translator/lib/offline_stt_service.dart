import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';
import 'package:path_provider/path_provider.dart';

class OfflineSttService {
  static const _modelAsset = 'assets/models/ethio_stt/model_quantized.onnx';
  static const _vocabAsset = 'assets/models/ethio_stt/vocab.json';
  static const _melFiltersAsset = 'assets/models/ethio_stt/mel_filters.bin';
  static const _windowAsset = 'assets/models/ethio_stt/window.bin';
  static const _sampleRate = 16000;
  static const _frameLength = 400;
  static const _hopLength = 160;
  static const _melBins = 80;
  static const _fftBins = 257;

  // Precomputed tables for 512-point Cooley-Tukey Radix-2 FFT
  static final List<int> _bitRev = () {
    final rev = List<int>.filled(512, 0);
    for (var i = 0; i < 512; i++) {
      var n = i;
      var r = 0;
      for (var b = 0; b < 9; b++) {
        r = (r << 1) | (n & 1);
        n >>= 1;
      }
      rev[i] = r;
    }
    return rev;
  }();

  static final Float64List _cosTable = () {
    final t = Float64List(256);
    for (var k = 0; k < 256; k++) {
      t[k] = math.cos(2 * math.pi * k / 512.0);
    }
    return t;
  }();

  static final Float64List _sinTable = () {
    final t = Float64List(256);
    for (var k = 0; k < 256; k++) {
      t[k] = math.sin(2 * math.pi * k / 512.0);
    }
    return t;
  }();

  OrtSession? _session;
  List<String>? _vocabulary;
  Float32List? _melFilters;
  Float32List? _window;

  Future<void> initialize() async {
    if (_session != null && _melFilters != null && _window != null) return;

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

    final options = OrtSessionOptions()
      ..setIntraOpNumThreads(4)
      ..setInterOpNumThreads(1)
      ..setSessionGraphOptimizationLevel(GraphOptimizationLevel.ortEnableBasic);
    _session = OrtSession.fromFile(modelFile, options);

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

    // 2. Mel filters (257 x 80 float32)
    if (_melFilters == null) {
      final externalMel =
          File('/sdcard/lisan_models/ethio_stt/mel_filters.bin');
      if (await externalMel.exists()) {
        final bytes = await externalMel.readAsBytes();
        _melFilters = bytes.buffer.asFloat32List(
          bytes.offsetInBytes,
          bytes.lengthInBytes ~/ 4,
        );
      } else {
        final data = await rootBundle.load(_melFiltersAsset);
        _melFilters = data.buffer.asFloat32List(
          data.offsetInBytes,
          data.lengthInBytes ~/ 4,
        );
      }
    }

    // 3. Povey window (400 float32)
    if (_window == null) {
      final externalWin = File('/sdcard/lisan_models/ethio_stt/window.bin');
      if (await externalWin.exists()) {
        final bytes = await externalWin.readAsBytes();
        _window = bytes.buffer.asFloat32List(
          bytes.offsetInBytes,
          bytes.lengthInBytes ~/ 4,
        );
      } else {
        final data = await rootBundle.load(_windowAsset);
        _window = data.buffer.asFloat32List(
          data.offsetInBytes,
          data.lengthInBytes ~/ 4,
        );
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
      final samples = _readWavPcm16(bytes);
      if (samples.isEmpty) {
        debugPrint('[Offline STT] Audio samples are empty');
        return '';
      }

      final features = _extractFeatures(samples);
      final tensor = OrtValueTensor.createTensorWithDataList(features.values, [
        1,
        features.frames,
        _melBins * 2,
      ]);
      final runOptions = OrtRunOptions();
      List<OrtValue?>? outputs;
      try {
        outputs = await _session!.runAsync(runOptions, {
          'input_features': tensor,
        });
      } finally {
        runOptions.release();
        tensor.release();
      }

      if (outputs == null || outputs.isEmpty) return '';
      final logits = outputs.first?.value;
      for (final output in outputs) {
        output?.release();
      }
      if (logits is! List) return '';
      final decoded = _decodeGreedy(logits);
      debugPrint('[Offline STT Decoded] "$decoded"');
      return decoded;
    } catch (e, st) {
      debugPrint('[Offline STT Error] $e\n$st');
      rethrow;
    }
  }

  List<double> _readWavPcm16(Uint8List bytes) {
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
    final samples = List<double>.filled(sampleCount, 0);
    for (var index = 0; index < sampleCount; index++) {
      var sum = 0.0;
      for (var channel = 0; channel < channels; channel++) {
        final position = dataStart + (index * frameBytes) + (channel * 2);
        sum += _i16(bytes, position);
      }
      // 16-bit PCM amplitude (-32768 to 32767)
      samples[index] = sum / channels;
    }
    return samples;
  }

  _FeatureMatrix _extractFeatures(List<double> samples) {
    final numFrames =
        1 + math.max(0, samples.length - _frameLength) ~/ _hopLength;
    final melFilters = _melFilters!;
    final window = _window!;

    // Shape: [numFrames * 80]
    final fbank = Float32List(numFrames * _melBins);
    final buffer = Float64List(512);

    for (var f = 0; f < numFrames; f++) {
      final start = f * _hopLength;

      // 1. Copy 400 samples and compute mean
      var sum = 0.0;
      for (var i = 0; i < _frameLength; i++) {
        final s = (start + i < samples.length) ? samples[start + i] : 0.0;
        buffer[i] = s;
        sum += s;
      }
      final mean = sum / _frameLength;

      // 2. Remove DC offset
      for (var i = 0; i < _frameLength; i++) {
        buffer[i] -= mean;
      }

      // 3. Preemphasis in reverse order so buffer[i - 1] is never overwritten
      for (var i = _frameLength - 1; i > 0; i--) {
        buffer[i] -= 0.97 * buffer[i - 1];
      }
      buffer[0] *= (1.0 - 0.97);

      // 4. Windowing
      for (var i = 0; i < _frameLength; i++) {
        buffer[i] *= window[i];
      }
      // Zero-pad to 512
      for (var i = _frameLength; i < 512; i++) {
        buffer[i] = 0.0;
      }

      // 5. 512-point FFT & Power Spectrum (unnormalized, matching numpy rfft)
      final power = _powerSpectrum(buffer);

      // 6. Mel filterbank multiplication (257 bins -> 80 mel channels)
      for (var mel = 0; mel < _melBins; mel++) {
        var energy = 0.0;
        for (var bin = 0; bin < _fftBins; bin++) {
          energy += power[bin] * melFilters[bin * _melBins + mel];
        }
        fbank[f * _melBins + mel] =
            math.log(math.max(energy, 1.192092955078125e-7));
      }
    }

    // 7. Per-mel normalization across all frames (ddof=1)
    for (var mel = 0; mel < _melBins; mel++) {
      var sum = 0.0;
      for (var f = 0; f < numFrames; f++) {
        sum += fbank[f * _melBins + mel];
      }
      final mean = sum / numFrames;

      var varSum = 0.0;
      for (var f = 0; f < numFrames; f++) {
        final diff = fbank[f * _melBins + mel] - mean;
        varSum += diff * diff;
      }
      final variance = numFrames > 1 ? varSum / (numFrames - 1) : 1.0;
      final std = math.sqrt(variance + 1e-7);

      for (var f = 0; f < numFrames; f++) {
        fbank[f * _melBins + mel] =
            (fbank[f * _melBins + mel] - mean) / std;
      }
    }

    // 8. Stride 2 concatenation: [usableFrames ~/ 2, 160]
    final usableFrames = numFrames - (numFrames % 2);
    final outputFrames = math.max(1, usableFrames ~/ 2);
    final features = Float32List(outputFrames * _melBins * 2);
    var writeIndex = 0;
    for (var f = 0; f < usableFrames; f += 2) {
      // Frame f (all 80 mel channels)
      for (var mel = 0; mel < _melBins; mel++) {
        features[writeIndex++] = fbank[f * _melBins + mel];
      }
      // Frame f + 1 (all 80 mel channels)
      for (var mel = 0; mel < _melBins; mel++) {
        features[writeIndex++] = fbank[(f + 1) * _melBins + mel];
      }
    }

    return _FeatureMatrix(features, outputFrames);
  }

  Float64List _powerSpectrum(Float64List signal) {
    final real = Float64List(512);
    final imag = Float64List(512);

    for (var i = 0; i < 512; i++) {
      real[_bitRev[i]] = signal[i];
    }

    for (var len = 2; len <= 512; len <<= 1) {
      final half = len >> 1;
      final step = 512 ~/ len;
      for (var i = 0; i < 512; i += len) {
        for (var k = 0; k < half; k++) {
          final tableIdx = k * step;
          final c = _cosTable[tableIdx];
          final s = _sinTable[tableIdx];
          final j = i + k + half;
          final rj = real[j];
          final ij = imag[j];
          final tr = c * rj + s * ij;
          final ti = c * ij - s * rj;
          real[j] = real[i + k] - tr;
          imag[j] = imag[i + k] - ti;
          real[i + k] += tr;
          imag[i + k] += ti;
        }
      }
    }

    final result = Float64List(_fftBins);
    for (var bin = 0; bin < _fftBins; bin++) {
      final r = real[bin];
      final im = imag[bin];
      result[bin] = r * r + im * im;
    }
    return result;
  }

  String _decodeGreedy(dynamic rawLogits) {
    final vocabulary = _vocabulary!;
    final sequence = rawLogits is List && rawLogits.isNotEmpty
        ? rawLogits[0] as List
        : const [];
    var previous = -1;
    final output = StringBuffer();
    const padTokenId = 408;

    for (final frame in sequence) {
      if (frame is! List || frame.isEmpty) continue;
      var best = 0;
      for (var index = 1; index < frame.length; index++) {
        if ((frame[index] as num) > (frame[best] as num)) best = index;
      }
      if (best != padTokenId) {
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

  String _ascii(Uint8List bytes, int start, int length) =>
      String.fromCharCodes(bytes.sublist(start, start + length));

  int _u16(Uint8List bytes, int offset) =>
      bytes[offset] | (bytes[offset + 1] << 8);

  int _u32(Uint8List bytes, int offset) =>
      bytes[offset] |
      (bytes[offset + 1] << 8) |
      (bytes[offset + 2] << 16) |
      (bytes[offset + 3] << 24);

  int _i16(Uint8List bytes, int offset) {
    final value = _u16(bytes, offset);
    return value >= 0x8000 ? value - 0x10000 : value;
  }

  void dispose() {
    _session?.release();
    _session = null;
  }
}

class _FeatureMatrix {
  const _FeatureMatrix(this.values, this.frames);

  final Float32List values;
  final int frames;
}
