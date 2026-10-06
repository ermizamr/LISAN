import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

class TranslatorApi {
  TranslatorApi({Uri? baseUri, http.Client? client})
    : baseUri = baseUri ?? Uri.parse('http://127.0.0.1:8000'),
      _client = client ?? http.Client();

  Uri baseUri;
  final http.Client _client;


  Future<bool> isReady() async {
    final response = await _client.get(baseUri.resolve('/health'));
    if (response.statusCode != 200) {
      return false;
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    return body['ready'] == true;
  }

  Future<Map<String, LanguageInfo>> fetchLanguages() async {
    final response = await _client.get(baseUri.resolve('/languages'));
    _ensureSuccess(response);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    return body.map((key, value) {
      final language = value as Map<String, dynamic>;
      return MapEntry(
        key,
        LanguageInfo(
          name: language['name'] as String,
          nativeName: language['native'] as String,
          flag: language['flag'] as String,
        ),
      );
    });
  }

  Future<TranslationResult> translateText({
    required String text,
    required String source,
    required String target,
    String? sessionId,
    String formality = 'auto',
  }) async {
    final response = await _client.post(
      baseUri.resolve('/translate/text'),
      headers: {'content-type': 'application/json'},
      body: jsonEncode({
        'text': text,
        'src': source,
        'tgt': target,
        'session_id': ?sessionId,
        'formality': formality,
      }),
    );
    _ensureSuccess(response);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final rawReplies = (body['suggested_replies'] as List<dynamic>?) ?? [];
    return TranslationResult(
      sourceText: body['source_text'] as String,
      translatedText: body['translated_text'] as String,
      sourceLanguage: body['src_lang'] as String,
      targetLanguage: body['tgt_lang'] as String,
      latencySeconds: (body['latency_seconds'] as num).toDouble(),
      intent: body['intent'] as String? ?? 'general_conversation',
      formality: body['formality'] as String? ?? 'auto',
      suggestedReplies: rawReplies
          .map((e) => QuickReplyItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      confidence: (body['confidence'] as num?)?.toDouble() ?? 0.90,
      isTmMatch: body['is_tm_match'] as bool? ?? false,
      entitiesPreserved: (body['entities_preserved'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      warning: body['warning'] as String?,
    );
  }

  Future<TranslationResult> translateAudio({
    required String filePath,
    required String source,
    required String target,
    String? sessionId,
    String formality = 'auto',
    String speakerMode = 'auto',
  }) async {
    final qParams = <String, String>{
      'src': source,
      'tgt': target,
      'formality': formality,
      'speaker_mode': speakerMode,
    };
    if (sessionId != null) {
      qParams['session_id'] = sessionId;
    }
    final request = http.MultipartRequest(
      'POST',
      baseUri.replace(
        path: '${baseUri.path}/translate/audio',
        queryParameters: qParams,
      ),
    )..files.add(await http.MultipartFile.fromPath('file', filePath));

    final response = await http.Response.fromStream(
      await _client.send(request),
    );
    _ensureSuccess(response);
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final rawReplies = (body['suggested_replies'] as List<dynamic>?) ?? [];
    return TranslationResult(
      sourceText: body['source_text'] as String,
      translatedText: body['translated_text'] as String,
      sourceLanguage: body['src_lang'] as String,
      targetLanguage: body['tgt_lang'] as String,
      latencySeconds: (body['latency_seconds'] as num).toDouble(),
      intent: body['intent'] as String? ?? 'general_conversation',
      formality: body['formality'] as String? ?? 'auto',
      suggestedReplies: rawReplies
          .map((e) => QuickReplyItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      confidence: (body['confidence'] as num?)?.toDouble() ?? 0.90,
      isTmMatch: body['is_tm_match'] as bool? ?? false,
      entitiesPreserved: (body['entities_preserved'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      warning: body['warning'] as String?,
    );
  }

  Uri getTtsUri(String text, String lang) {
    return baseUri.replace(
      path: '${baseUri.path}/tts'.replaceAll('//', '/'),
      queryParameters: {'text': text, 'lang': lang},
    );
  }

  Future<Uint8List> synthesizeSpeech(String text, String lang) async {
    final uri = getTtsUri(text, lang);
    final response = await _client.get(uri);
    _ensureSuccess(response);
    return response.bodyBytes;
  }

  void _ensureSuccess(http.Response response) {
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw TranslatorApiException(response.statusCode, response.body);
    }
  }

  void dispose() => _client.close();
}

class LanguageInfo {
  const LanguageInfo({
    required this.name,
    required this.nativeName,
    required this.flag,
  });

  final String name;
  final String nativeName;
  final String flag;
}

class QuickReplyItem {
  const QuickReplyItem({
    required this.text,
    required this.translation,
  });

  final String text;
  final String translation;

  factory QuickReplyItem.fromJson(Map<String, dynamic> json) {
    return QuickReplyItem(
      text: json['text'] as String? ?? '',
      translation: json['translation'] as String? ?? '',
    );
  }
}

class TranslationResult {
  const TranslationResult({
    required this.sourceText,
    required this.translatedText,
    required this.sourceLanguage,
    required this.targetLanguage,
    required this.latencySeconds,
    this.intent = 'general_conversation',
    this.formality = 'auto',
    this.suggestedReplies = const [],
    this.confidence = 0.90,
    this.isTmMatch = false,
    this.entitiesPreserved = const [],
    this.warning,
  });

  final String sourceText;
  final String translatedText;
  final String sourceLanguage;
  final String targetLanguage;
  final double latencySeconds;
  final String intent;
  final String formality;
  final List<QuickReplyItem> suggestedReplies;
  final double confidence;
  final bool isTmMatch;
  final List<String> entitiesPreserved;
  final String? warning;
}

class TranslatorApiException implements Exception {
  const TranslatorApiException(this.statusCode, this.body);

  final int statusCode;
  final String body;

  @override
  String toString() => 'TranslatorApiException($statusCode): $body';
}
