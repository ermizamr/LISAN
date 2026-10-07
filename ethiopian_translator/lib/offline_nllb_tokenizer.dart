import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart';

class OfflineNllbTokenizer {
  static const _asset = 'assets/models/nllb/tokenizer.json';

  Map<String, int>? _vocabulary;
  Map<String, int>? _mergeRanks;
  List<String>? _idToToken;

  Future<void> initialize() async {
    if (_vocabulary != null) return;

    String jsonString;
    final externalJson = File('/sdcard/lisan_models/nllb/tokenizer.json');
    if (await externalJson.exists()) {
      jsonString = await externalJson.readAsString();
    } else {
      jsonString = await rootBundle.loadString(_asset);
    }

    final root = jsonDecode(jsonString) as Map<String, dynamic>;
    final model = root['model'] as Map<String, dynamic>;
    final rawVocabulary = model['vocab'] as Map<String, dynamic>;
    _vocabulary = rawVocabulary.map((token, id) => MapEntry(token, id as int));
    _idToToken = List<String>.filled(
      _vocabulary!.values.reduce((a, b) => a > b ? a : b) + 1,
      '<unk>',
    );
    for (final entry in _vocabulary!.entries) {
      _idToToken![entry.value] = entry.key;
    }

    final merges = (model['merges'] as List<dynamic>?) ?? const [];
    _mergeRanks = <String, int>{};
    for (var index = 0; index < merges.length; index++) {
      final item = merges[index];
      if (item is List && item.length >= 2) {
        _mergeRanks!['${item[0]} ${item[1]}'] = index;
      } else {
        _mergeRanks![item.toString()] = index;
      }
    }
  }

  Future<List<int>> encode(String text, String sourceLanguage) async {
    await initialize();
    final sourceId = _vocabulary![sourceLanguage];
    if (sourceId == null) {
      throw ArgumentError('Unsupported source language: $sourceLanguage');
    }

    final ids = <int>[sourceId];
    final normalized = text.replaceAll(RegExp(r' {2,}'), ' ').trim();
    if (normalized.isNotEmpty) {
      for (final piece in _metaspacePieces(normalized)) {
        for (final token in _bpe(piece)) {
          ids.add(_vocabulary![token] ?? _vocabulary!['<unk>']!);
        }
      }
    }
    ids.add(_vocabulary!['</s>']!);
    return ids;
  }

  /// Returns the vocabulary ID for [token], or null if not found.
  /// Call after [initialize()] or it will return null.
  int? tokenToId(String token) => _vocabulary?[token];

  Future<String> decode(List<int> ids) async {
    await initialize();
    final text = StringBuffer();
    for (final id in ids) {
      if (id < 0 || id >= _idToToken!.length) continue;
      final token = _idToToken![id];
      if (token == '</s>' || token == '<pad>' || token == '<s>') continue;
      if (token.startsWith('[') && token.endsWith(']')) continue;
      text.write(token);
    }
    return text.toString().replaceAll('\u2581', ' ').trim();
  }

  List<String> _metaspacePieces(String text) {
    final marked = '\u2581${text.replaceAll(' ', '\u2581')}';
    final pieces = <String>[];
    var start = 0;
    for (var index = 1; index < marked.length; index++) {
      if (marked[index] == '\u2581') {
        pieces.add(marked.substring(start, index));
        start = index;
      }
    }
    pieces.add(marked.substring(start));
    return pieces.where((piece) => piece.isNotEmpty).toList();
  }

  List<String> _bpe(String piece) {
    var symbols = piece.runes.map(String.fromCharCode).toList();
    while (symbols.length > 1) {
      var bestRank = 1 << 30;
      var bestIndex = -1;
      for (var index = 0; index < symbols.length - 1; index++) {
        final rank = _mergeRanks!['${symbols[index]} ${symbols[index + 1]}'];
        if (rank != null && rank < bestRank) {
          bestRank = rank;
          bestIndex = index;
        }
      }
      if (bestIndex < 0) break;
      symbols[bestIndex] = symbols[bestIndex] + symbols.removeAt(bestIndex + 1);
    }
    return symbols;
  }
}
