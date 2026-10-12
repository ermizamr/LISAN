import 'package:ethiopian_translator/offline_nllb_tokenizer.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('encodes NLLB language framing and decodes tokens', () async {
    final tokenizer = OfflineNllbTokenizer();
    final ids = await tokenizer.encode('Hello', 'eng_Latn');

    expect(ids.first, 26127);
    expect(ids.last, 2);
    expect(await tokenizer.decode(ids), contains('Hello'));
  });

  test('encodes and decodes Amharic sentence', () async {
    final tokenizer = OfflineNllbTokenizer();
    final ids = await tokenizer.encode('ሰላም እንዴት ነህ?', 'amh_Ethi');
    expect(ids, [26126, 14403, 8577, 20058, 25617, 2]);
    final decoded = await tokenizer.decode(ids.sublist(1, ids.length - 1));
    expect(decoded, 'ሰላም እንዴት ነህ?');
  });

  test('encodes and decodes Tigrinya sentence', () async {
    final tokenizer = OfflineNllbTokenizer();
    final ids = await tokenizer.encode('ሰላም ከመይ ኣለኻ?', 'tir_Ethi');
    expect(ids.first, 26130);
    expect(ids.last, 2);
    final decoded = await tokenizer.decode(ids.sublist(1, ids.length - 1));
    expect(decoded, 'ሰላም ከመይ ኣለኻ?');
  });

  test('encodes and decodes Oromo sentence', () async {
    final tokenizer = OfflineNllbTokenizer();
    final ids = await tokenizer.encode('Nagaa akkam jirta?', 'gaz_Latn');
    expect(ids.first, 26128);
    expect(ids.last, 2);
    final decoded = await tokenizer.decode(ids.sublist(1, ids.length - 1));
    expect(decoded, 'Nagaa akkam jirta?');
  });

  test('encodes and decodes Somali sentence', () async {
    final tokenizer = OfflineNllbTokenizer();
    final ids = await tokenizer.encode('Sidee tahay?', 'som_Latn');
    expect(ids.first, 26129);
    expect(ids.last, 2);
    final decoded = await tokenizer.decode(ids.sublist(1, ids.length - 1));
    expect(decoded, 'Sidee tahay?');
  });
}
