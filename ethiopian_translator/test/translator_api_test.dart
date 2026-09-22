import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'package:ethiopian_translator/translator_api.dart';

void main() {
  test('translates text using the FastAPI response contract', () async {
    final client = MockClient((request) async {
      expect(request.method, 'POST');
      expect(request.url.path, '/translate/text');
      return http.Response.bytes(
        utf8.encode(
          '{"source_text":"Hello","translated_text":"ሰላም","src_lang":"eng","tgt_lang":"amh","latency_seconds":0.42}',
        ),
        200,
        headers: {'content-type': 'application/json; charset=utf-8'},
      );
    });
    final api = TranslatorApi(client: client);

    final result = await api.translateText(
      text: 'Hello',
      source: 'eng',
      target: 'amh',
    );

    expect(result.sourceText, 'Hello');
    expect(result.translatedText, 'ሰላም');
    expect(result.latencySeconds, 0.42);
    api.dispose();
  });

  test('reports API errors with status and response body', () async {
    final api = TranslatorApi(
      client: MockClient(
        (_) async => http.Response('unsupported language', 400),
      ),
    );

    expect(() => api.fetchLanguages(), throwsA(isA<TranslatorApiException>()));
    api.dispose();
  });
}
