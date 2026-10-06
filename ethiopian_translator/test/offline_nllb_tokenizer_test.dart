import 'package:ethiopian_translator/offline_nllb_tokenizer.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('encodes NLLB language framing and decodes tokens', () async {
    final tokenizer = OfflineNllbTokenizer();
    final ids = await tokenizer.encode('Hello', 'eng_Latn');

    expect(ids.first, 256047);
    expect(ids.last, 2);
    expect(await tokenizer.decode(ids), contains('Hello'));
  });
}
