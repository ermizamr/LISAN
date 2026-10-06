import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';
import 'package:path_provider/path_provider.dart';

class OfflineSttService {
  static const _modelAsset = 'assets/models/ethio_stt/model_quantized.onnx';
  static const _vocabAsset = 'assets/models/ethio_stt/vocab.json';
  static const _sampleRate = 16000;
  static const _frameLength = 400;
  static const _hopLength = 160;
  static const _melBins = 80;
  static const _fftBins = 257;

  OrtSession? _session;
  List<String>? _vocabulary;

  Future<void> initialize() async {
    if (_session != null) return;

    final directory = await getApplicationSupportDirectory();
    final modelFile = File('${directory.path}/ethio_stt_model_quantized.onnx');
    if (!await modelFile.exists()) {
      final modelBytes = await rootBundle.load(_modelAsset);
      await modelFile.writeAsBytes(
        modelBytes.buffer.asUint8List(),
        flush: true,
      );
    }

    final options = OrtSessionOptions()
      ..setIntraOpNumThreads(2)
      ..setInterOpNumThreads(1);
    _session = OrtSession.fromFile(modelFile, options);

    final vocabJson = await rootBundle.loadString(_vocabAsset);
    final vocab = (jsonDecode(vocabJson) as Map<String, dynamic>);
    final maxId = vocab.values.cast<int>().reduce(math.max);
    _vocabulary = List<String>.filled(maxId + 1, '');
    for (final entry in vocab.entries) {
      _vocabulary![entry.value as int] = entry.key;
    }
  }

  Future<String> transcribe(String wavPath) async {
    await initialize();
    final samples = _readWavPcm16(File(wavPath).readAsBytesSync());
    if (samples.isEmpty) return '';

    final features = _extractFeatures(samples);
    final tensor = OrtValueTensor.createTensorWithDataList(features.values, [
      1,
      features.frames,
      _melBins * 2,
    ]);
    final runOptions = OrtRunOptions();
    final outputs = await _session!.runAsync(runOptions, {
      'input_features': tensor,
    });
    runOptions.release();
    tensor.release();

    final logits = outputs?.first?.value;
    for (final output in outputs ?? const <OrtValue?>[]) {
      output?.release();
    }
    if (logits is! List) return '';
    return _decodeGreedy(logits);
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
        sum += _i16(bytes, position) / 32768.0;
      }
      samples[index] = sum / channels;
    }
    return samples;
  }

  _FeatureMatrix _extractFeatures(List<double> samples) {
    final frameCount = math.max(
      1,
      1 + math.max(0, samples.length - _frameLength) ~/ _hopLength,
    );
    final filters = _melFilterBank();
    final features = <double>[];
    final perBin = List.generate(_melBins, (_) => <double>[]);
    final window = List<double>.generate(
      _frameLength,
      (index) => math
          .pow(
            0.5 - 0.5 * math.cos(2 * math.pi * index / (_frameLength - 1)),
            0.85,
          )
          .toDouble(),
    );

    for (var frame = 0; frame < frameCount; frame++) {
      final start = frame * _hopLength;
      final signal = List<double>.filled(_frameLength, 0);
      var mean = 0.0;
      for (var index = 0; index < _frameLength; index++) {
        final sample = start + index < samples.length
            ? samples[start + index]
            : 0.0;
        mean += sample;
        signal[index] = sample;
      }
      mean /= _frameLength;
      for (var index = 0; index < _frameLength; index++) {
        final previous = index == 0 ? signal[index] : signal[index - 1];
        signal[index] =
            (signal[index] - mean - 0.97 * (previous - mean)) *
            window[index] *
            32768.0;
      }

      final power = _powerSpectrum(signal);
      for (var mel = 0; mel < _melBins; mel++) {
        var energy = 0.0;
        for (var bin = 0; bin < _fftBins; bin++) {
          energy += power[bin] * filters[mel][bin];
        }
        perBin[mel].add(math.log(math.max(energy, 1.192092955078125e-7)));
      }
    }

    for (final bin in perBin) {
      final mean = bin.reduce((a, b) => a + b) / bin.length;
      final variance = bin.length > 1
          ? bin
                    .map((value) => math.pow(value - mean, 2))
                    .reduce((a, b) => a + b) /
                (bin.length - 1)
          : 1.0;
      for (var index = 0; index < bin.length; index++) {
        bin[index] = (bin[index] - mean) / math.sqrt(variance + 1e-7);
      }
    }

    final usableFrames = frameCount - (frameCount % 2);
    for (var frame = 0; frame < usableFrames; frame += 2) {
      for (var mel = 0; mel < _melBins; mel++) {
        features.add(perBin[mel][frame]);
        features.add(perBin[mel][frame + 1]);
      }
    }
    if (features.isEmpty) {
      features.addAll(List<double>.filled(_melBins * 2, 0));
    }
    return _FeatureMatrix(features, math.max(1, usableFrames ~/ 2));
  }

  List<double> _powerSpectrum(List<double> signal) {
    final result = List<double>.filled(_fftBins, 0);
    for (var bin = 0; bin < _fftBins; bin++) {
      var real = 0.0;
      var imaginary = 0.0;
      for (var sample = 0; sample < _frameLength; sample++) {
        final angle = 2 * math.pi * bin * sample / 512.0;
        real += signal[sample] * math.cos(angle);
        imaginary -= signal[sample] * math.sin(angle);
      }
      result[bin] = (real * real + imaginary * imaginary) / 512.0;
    }
    return result;
  }

  List<List<double>> _melFilterBank() {
    final filters = List.generate(
      _melBins,
      (_) => List<double>.filled(_fftBins, 0),
    );
    final lowMel = 1127.0 * math.log(1 + 20 / 700.0);
    final highMel = 1127.0 * math.log(1 + 8000 / 700.0);
    final points = List<int>.generate(_melBins + 2, (index) {
      final mel = lowMel + (highMel - lowMel) * index / (_melBins + 1);
      final hz = 700.0 * (math.exp(mel / 1127.0) - 1);
      return (513 * hz / _sampleRate).floor().clamp(0, _fftBins - 1);
    });
    for (var mel = 0; mel < _melBins; mel++) {
      final left = points[mel];
      final center = points[mel + 1];
      final right = points[mel + 2];
      for (var bin = left; bin < center; bin++) {
        if (center > left) filters[mel][bin] = (bin - left) / (center - left);
      }
      for (var bin = center; bin <= right; bin++) {
        if (right > center) {
          filters[mel][bin] = (right - bin) / (right - center);
        }
      }
    }
    return filters;
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
      if (best != 0 && best != previous && best < vocabulary.length) {
        final token = vocabulary[best];
        if (!token.startsWith('[') && token != '[PAD]' && token != '[UNK]') {
          output.write(token == '|' ? ' ' : token);
        }
      }
      previous = best;
    }
    return output.toString().trim();
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

  final List<double> values;
  final int frames;
}
