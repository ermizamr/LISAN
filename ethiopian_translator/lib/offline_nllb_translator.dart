import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:onnxruntime/onnxruntime.dart';
import 'package:path_provider/path_provider.dart';
import 'offline_ort_config.dart';

import 'offline_nllb_tokenizer.dart';
import 'offline_translation_memory.dart';

/// NLLB language token → FLORES-200 language code mapping.
/// These are the language tokens used in the tokenizer vocabulary.
const Map<String, String> kNllbLangTokens = {
  'amh': 'amh_Ethi',
  'orm': 'gaz_Latn',
  'tir': 'tir_Ethi',
  'som': 'som_Latn',
  'eng': 'eng_Latn',
};

/// Runs offline NLLB-200 translation using quantized ONNX models.
///
/// Uses encoder + decoder_with_past pattern for efficient generation.
/// Models are copied from assets to app support dir on first use.
class OfflineNllbTranslator {
  static const _encoderAsset =
      'assets/models/nllb/encoder_model_quantized.onnx';
  static const _decoderAsset =
      'assets/models/nllb/decoder_model_quantized.onnx';

  static const int _bosTokenId = 0; // <s>
  static const int _eosTokenId = 2; // </s>
  static const int _padTokenId = 1; // <pad>
  static const int _maxNewTokens = 24;

  final OfflineNllbTokenizer _tokenizer = OfflineNllbTokenizer();

  bool get isInitialized => true;

  Future<void> initializeTokenizer() => _tokenizer.initialize();

  Future<void> initialize() async {
    final dir = await getApplicationSupportDirectory();
    await _ensureModel(dir, _encoderAsset, 'nllb_encoder.onnx');
    await _ensureModel(dir, _decoderAsset, 'nllb_decoder.onnx');
    await _tokenizer.initialize();
  }


  Future<File> _ensureModel(
    Directory dir,
    String asset,
    String filename,
  ) async {
    // 1. Check external sdcard directory
    final externalCandidates = [
      File('/sdcard/lisan_models/nllb/$filename'),
      File('/sdcard/lisan_models/nllb/${filename.replaceAll('nllb_', '').replaceAll('.onnx', '_model_quantized.onnx')}'),
      File('/sdcard/lisan_models/nllb/${filename.replaceAll('nllb_', '')}'),
    ];
    for (final ext in externalCandidates) {
      if (await ext.exists()) {
        debugPrint('[Offline NMT] Using model from ${ext.path}');
        return ext;
      }
    }

    // 2. Check app support directory
    final file = File('${dir.path}/$filename');
    if (await file.exists()) {
      return file;
    }

    // 3. Fallback: try loading from assets
    try {
      final bytes = await rootBundle.load(asset);
      await file.writeAsBytes(bytes.buffer.asUint8List(), flush: true);
      return file;
    } catch (e) {
      debugPrint('[Offline NMT] Asset note for $filename: $e');
      throw StateError('Model $filename not found on /sdcard or assets');
    }
  }

  /// Translate [text] from [sourceLang] to [targetLang].
  /// Lang codes are backend keys: 'amh', 'orm', 'tir', 'som', 'eng'.
  Future<String> translate(
    String text, {
    required String sourceLang,
    required String targetLang,
    bool bypassTm = false,
  }) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return '';

    // If source and target languages are identical, return unchanged text
    if (sourceLang == targetLang) {
      return trimmed;
    }

    // High-speed Translation Memory & Curated Medical/Conversational Glossary
    if (!bypassTm) {
      final tmHit = OfflineTranslationMemory.lookupWithRepair(
        trimmed,
        sourceLang: sourceLang,
        targetLang: targetLang,
      );
      if (tmHit != null) {
        debugPrint('[Offline TM Hit] "$trimmed" -> "${tmHit.translation}" (Repaired: "${tmHit.repairedSource}")');
        return tmHit.translation;
      }
    }

    final dir = await getApplicationSupportDirectory();
    final encoderFile = await _ensureModel(dir, _encoderAsset, 'nllb_encoder.onnx');
    final decoderFile = await _ensureModel(dir, _decoderAsset, 'nllb_decoder.onnx');

    final sourceToken =
        kNllbLangTokens[sourceLang] ??
        (throw ArgumentError('Unknown source lang: $sourceLang'));
    final targetToken =
        kNllbLangTokens[targetLang] ??
        (throw ArgumentError('Unknown target lang: $targetLang'));

    // Normalize source text before feeding into NLLB tokenizer
    final inputToEncode = OfflineTranslationMemory.normalizeForNmt(trimmed, sourceLang);
    if (inputToEncode != trimmed) {
      debugPrint('[Offline NMT] Pre-normalized ($sourceLang): "$trimmed" -> "$inputToEncode"');
    }

    // 1. Tokenize source
    final inputIds = await _tokenizer.encode(inputToEncode, sourceToken);
    final seqLen = inputIds.length;

    // 2. Sequential Step 1: Run Encoder Session Only
    final inputIdsTensor = _int64Tensor(inputIds, [1, seqLen]);
    final attentionMask = _int64Tensor(List.filled(seqLen, 1), [1, seqLen]);

    dynamic rawEncoderHiddenStates;
    final encOptions = OfflineOrtConfig.createOptions(
      intraOpThreads: 2,
      interOpThreads: 1,
    );
    OrtSession? encoderSession;
    try {
      debugPrint('[Offline NMT] [Governor] Loading encoder session...');
      encoderSession = OrtSession.fromFile(encoderFile, encOptions);
      final encRunOptions = OrtRunOptions();
      try {
        final encoderOutputs = encoderSession.run(
          encRunOptions,
          {
            'input_ids': inputIdsTensor,
            'attention_mask': attentionMask,
          },
        );
        rawEncoderHiddenStates = encoderOutputs.first?.value;
        for (final out in encoderOutputs) {
          out?.release();
        }
      } finally {
        encRunOptions.release();
      }
    } finally {
      encoderSession?.release();
      encoderSession = null;
      encOptions.release();
      inputIdsTensor.release();
      OfflineOrtConfig.trimNativeMemory();
      debugPrint('[Offline NMT] [Governor] Encoder freed & native heap trimmed ✓');
    }

    if (rawEncoderHiddenStates == null) {
      attentionMask.release();
      throw StateError('Encoder produced null hidden states');
    }

    // 3. Sequential Step 2: Prepare Target Framing & Decoder Input
    final targetLangId = _tokenizer.tokenToId(targetToken) ?? _bosTokenId;
    final currIds = <int>[_eosTokenId, targetLangId];

    final flattenedHidden = _flattenFloats(rawEncoderHiddenStates);
    final hiddenTensor = _float32Tensor(flattenedHidden, [1, seqLen, 1024]);

    final decOptions = OfflineOrtConfig.createOptions(
      intraOpThreads: 2,
      interOpThreads: 1,
    );
    OrtSession? decoderSession;
    try {
      debugPrint('[Offline NMT] [Governor] Loading decoder session...');
      decoderSession = OrtSession.fromFile(decoderFile, decOptions);
      final runOptions = OrtRunOptions();
      try {
        for (var step = 0; step < _maxNewTokens; step++) {
          final decoderInputIds = _int64Tensor(currIds, [1, currIds.length]);

          final stepOutputs = decoderSession.run(
            runOptions,
            {
              'input_ids': decoderInputIds,
              'encoder_attention_mask': attentionMask,
              'encoder_hidden_states': hiddenTensor,
            },
          );
          decoderInputIds.release();

          if (stepOutputs.isEmpty) break;

          final logitsTensor = stepOutputs.first;
          for (var i = 1; i < stepOutputs.length; i++) {
            stepOutputs[i]?.release();
          }

          final logits = logitsTensor?.value;
          logitsTensor?.release();

          final nextTokenId = _argmax(
            logits,
            currIds.length - 1,
            generatedIds: currIds,
          );
          currIds.add(nextTokenId);

          if (nextTokenId == _eosTokenId || nextTokenId == _padTokenId) {
            break;
          }
        }
      } finally {
        runOptions.release();
      }
    } finally {
      hiddenTensor.release();
      decoderSession?.release();
      decoderSession = null;
      decOptions.release();
      attentionMask.release();
      OfflineOrtConfig.trimNativeMemory();
      debugPrint('[Offline NMT] [Governor] Decoder freed & native heap trimmed ✓');
    }

    // 5. Decode generated tokens (skip initial prompt [2, targetLangId])
    final resultTokens = currIds.length > 2 ? currIds.sublist(2) : currIds;
    final rawTranslated = await _tokenizer.decode(resultTokens);
    return OfflineTranslationMemory.postprocess(
      rawTranslated,
      sourceLang: sourceLang,
      targetLang: targetLang,
    );
  }

  /// Argmax over last dimension with standard HuggingFace repetition penalty
  /// to eliminate degenerative repetition loops.
  int _argmax(
    dynamic logits,
    int stepIndex, {
    List<int>? generatedIds,
    double repetitionPenalty = 1.3,
  }) {
    List<dynamic> frame;
    if (logits is List && logits.isNotEmpty && logits[0] is List) {
      final batch = logits[0] as List;
      final idx = math.min(stepIndex, batch.length - 1);
      frame = batch[idx] is List ? batch[idx] as List<dynamic> : batch;
    } else if (logits is List) {
      frame = logits;
    } else {
      return _eosTokenId;
    }

    // Set of tokens already generated (skip prompt token)
    final prevTokens = generatedIds != null ? generatedIds.toSet() : const <int>{};

    var best = 0;
    var bestVal = -double.maxFinite;
    final len = frame.length;
    for (var i = 0; i < len; i++) {
      final num rawVal = frame[i] as num;
      var v = rawVal.toDouble();

      // Standard Hugging Face RepetitionPenaltyLogitsProcessor formula:
      // If token was already generated, divide positive logits by penalty, multiply negative logits
      if (prevTokens.contains(i)) {
        v = v > 0 ? v / repetitionPenalty : v * repetitionPenalty;
      }

      if (v > bestVal) {
        bestVal = v;
        best = i;
      }
    }
    return best;
  }

  static List<double> _flattenFloats(dynamic value) {
    final result = <double>[];
    void recurse(dynamic v) {
      if (v is List) {
        for (final item in v) {
          recurse(item);
        }
      } else if (v is num) {
        result.add(v.toDouble());
      }
    }
    recurse(value);
    return result;
  }

  OrtValueTensor _float32Tensor(List<double> data, List<int> shape) {
    final typed = Float32List.fromList(data);
    return OrtValueTensor.createTensorWithDataList([typed], shape);
  }

  OrtValueTensor _int64Tensor(List<int> data, List<int> shape) {
    final typed = Int64List.fromList(data);
    return OrtValueTensor.createTensorWithDataList(typed, shape);
  }

  void dispose() {
    OfflineOrtConfig.trimNativeMemory();
  }

}
