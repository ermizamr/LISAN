import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

/// Offline VITS tokenizer for Meta MMS-TTS.
///
/// Handles:
/// 1. Ethiopic-to-uroman phoneme/character transliteration for Amharic ('amh') and Tigrinya ('tir').
/// 2. Lowercasing and whitespace normalization.
/// 3. Character-to-ID mapping with blank pad token (0) interspersion ([0, c1, 0, c2, ..., 0]).
class OfflineVitsTokenizer {
  static final OfflineVitsTokenizer _instance = OfflineVitsTokenizer._internal();
  factory OfflineVitsTokenizer() => _instance;
  OfflineVitsTokenizer._internal();

  bool _initialized = false;
  bool get isInitialized => _initialized;

  // Language code -> (char -> token_id)
  final Map<String, Map<String, int>> _vocabularies = {};

  // Ethiopic char -> romanized string
  Map<String, String> _ethiopicToUroman = {};

  /// Initialize tokenizers for all supported languages ('amh', 'orm', 'tir', 'som', 'eng').
  Future<void> initialize() async {
    if (_initialized) return;

    // 1. Load Ethiopic-to-uroman transliteration table
    await _loadUromanTable();

    // 2. Load vocabularies for all 5 languages
    for (final lang in const ['amh', 'orm', 'tir', 'som', 'eng']) {
      await _loadVocab(lang);
    }

    _initialized = true;
    debugPrint('[OfflineVitsTokenizer] Initialized successfully for languages: ${_vocabularies.keys.toList()}');
  }

  Future<void> _loadUromanTable() async {
    try {
      String jsonStr;
      final externalFile = File('/sdcard/lisan_models/mms_tts/ethiopic_to_uroman.json');
      if (await externalFile.exists()) {
        jsonStr = await externalFile.readAsString();
      } else {
        jsonStr = await rootBundle.loadString('assets/models/mms_tts/ethiopic_to_uroman.json');
      }

      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      _ethiopicToUroman = parsed.map((k, v) => MapEntry(k, v.toString()));
      debugPrint('[OfflineVitsTokenizer] Loaded ${_ethiopicToUroman.length} Ethiopic uroman rules.');
    } catch (e) {
      debugPrint('[OfflineVitsTokenizer] Warning: Could not load external/asset uroman table ($e). Falling back to direct transliteration.');
      _ethiopicToUroman = {};
    }
  }

  Future<void> _loadVocab(String lang) async {
    try {
      String jsonStr;
      final externalFile = File('/sdcard/lisan_models/mms_tts/$lang/vocab.json');
      if (await externalFile.exists()) {
        jsonStr = await externalFile.readAsString();
      } else {
        jsonStr = await rootBundle.loadString('assets/models/mms_tts/$lang/vocab.json');
      }

      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final map = <String, int>{};
      for (final entry in parsed.entries) {
        if (entry.value is int) {
          map[entry.key] = entry.value as int;
        }
      }
      _vocabularies[lang] = map;
      debugPrint('[OfflineVitsTokenizer] Loaded $lang vocabulary: ${map.length} tokens.');
    } catch (e) {
      debugPrint('[OfflineVitsTokenizer] Warning: Could not load vocab for $lang ($e).');
    }
  }

  /// Transliterates Ethiopic script to lowercase Latin according to Meta MMS uroman mappings.
  String transliterateEthiopic(String text) {
    if (_ethiopicToUroman.isEmpty) {
      return text;
    }

    final sb = StringBuffer();
    for (final rune in text.runes) {
      final ch = String.fromCharCode(rune);
      final mapped = _ethiopicToUroman[ch];
      if (mapped != null) {
        sb.write(mapped);
      } else {
        sb.write(ch);
      }
    }
    return sb.toString();
  }

  /// Encodes input [text] for [lang] into token IDs with blank pad token interleaving.
  ///
  /// Output format: `[0, id_1, 0, id_2, 0, ..., id_n, 0]`
  List<int> encode(String text, String lang) {
    var processed = text.trim();
    if (processed.isEmpty) {
      return const [0, 0];
    }

    // Amharic and Tigrinya require Ethiopic -> Latin uroman transliteration
    if (lang == 'amh' || lang == 'tir') {
      processed = transliterateEthiopic(processed);
    }

    // Lowercase for character lookup
    processed = processed.toLowerCase();

    final vocab = _vocabularies[lang];
    if (vocab == null) {
      debugPrint('[OfflineVitsTokenizer] Warning: No vocab found for $lang, using fallback character encoding.');
      return _fallbackEncode(processed);
    }

    final ids = <int>[0]; // initial pad token
    for (int i = 0; i < processed.length; i++) {
      final ch = processed[i];
      final tokenId = vocab[ch];
      if (tokenId != null) {
        ids.add(tokenId);
        ids.add(0); // interleave blank pad token
      }
      // Characters not in vocab (like punctuation marks ?, !, .) are omitted, matching HuggingFace VitsTokenizer
    }

    if (ids.length <= 1) {
      // Nothing was in vocab, return minimal silence
      return const [0, 0];
    }

    return ids;
  }

  List<int> _fallbackEncode(String text) {
    final ids = <int>[0];
    for (final codeUnit in text.codeUnits) {
      ids.add(codeUnit % 30);
      ids.add(0);
    }
    return ids;
  }
}
