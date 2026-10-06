import 'dart:convert';

import 'package:flutter/services.dart';

class OfflineNllbTokenizer {
  static const _asset = 'assets/models/nllb/tokenizer.json';

  Map<String, int>? _vocabulary;
  Map<String, int>? _mergeRanks;
  List<String>? _idToToken;

  Future<void> initialize() async {
    if (_vocabulary != null) return;

    final root =
        jsonDecode(await rootBundle.loadString(_asset)) as Map<String, dynamic>;
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
      final merge = merges[index].toString();
      _mergeRanks![merge] = index;
    }
  }

  Future<List<int>> encode(String text, String sourceLanguage) async {
    await initialize();
    final sourceId = _vocabulary![sourceLanguage];
    if (sourceId == null)
      throw ArgumentError('Unsupported source language: $sourceLanguage');

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
    return text.toString().replaceAll('▁', ' ').trim();
  }

  List<String> _metaspacePieces(String text) {
    final marked = '▁${text.replaceAll(' ', '▁')}';
    final pieces = <String>[];
    var start = 0;
    for (var index = 1; index < marked.length; index++) {
      if (marked[index] == '▁') {
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
