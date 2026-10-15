import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

class TranslatorApi {
  TranslatorApi({Uri? baseUri, http.Client? client})
    : baseUri = baseUri ?? Uri.parse('http://127.0.0.1:8000'),
      _client = client ?? http.Client();

  Uri baseUri;
  final http.Client _client;

  static const String _envApiUrl = String.fromEnvironment('LISAN_API_URL', defaultValue: '');

  static final List<Uri> candidateBaseUris = [
    if (_envApiUrl.isNotEmpty) Uri.parse(_envApiUrl),
    Uri.parse('http://127.0.0.1:8000'),
    Uri.parse('http://10.0.2.2:8000'),
    Uri.parse('http://192.168.1.3:8000'),
  ];

  Future<bool> isReady() async {
    final urisToTry = [baseUri, ...candidateBaseUris.where((u) => u != baseUri)];
    for (final candidate in urisToTry) {
      try {
        final response = await _client.get(candidate.resolve('/health')).timeout(const Duration(milliseconds: 1200));
        if (response.statusCode == 200) {
          final body = jsonDecode(response.body) as Map<String, dynamic>;
          if (body['ready'] == true) {
            baseUri = candidate;
            return true;
          }
        }
      } catch (_) {}
    }
    return false;
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
    final payload = jsonEncode({
      'text': text,
      'src': source,
      'tgt': target,
      'session_id': sessionId,
      'formality': formality,
    });

    http.Response? response;
    dynamic lastError;
    final urisToTry = [baseUri, ...candidateBaseUris.where((u) => u != baseUri)];

    for (final candidate in urisToTry) {
      try {
        final res = await _client.post(
          candidate.resolve('/translate/text'),
          headers: {'content-type': 'application/json'},
          body: payload,
        ).timeout(const Duration(seconds: 15));
        if (res.statusCode == 200) {
          response = res;
          baseUri = candidate;
          break;
        }
      } catch (e) {
        lastError = e;
      }
    }

    if (response == null) {
      throw lastError ?? Exception('Failed to connect to backend server');
    }

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

    http.Response? response;
    dynamic lastError;
    final urisToTry = [baseUri, ...candidateBaseUris.where((u) => u != baseUri)];

    for (final candidate in urisToTry) {
      try {
        final request = http.MultipartRequest(
          'POST',
          candidate.resolve('/translate/audio').replace(
            queryParameters: qParams,
          ),
        )..files.add(await http.MultipartFile.fromPath('file', filePath));

        final streamed = await _client.send(request).timeout(const Duration(seconds: 20));
        final res = await http.Response.fromStream(streamed);
        if (res.statusCode == 200) {
          response = res;
          baseUri = candidate;
          break;
        }
      } catch (e) {
        lastError = e;
      }
    }

    if (response == null) {
      throw lastError ?? Exception('Failed to connect to backend server');
    }

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
