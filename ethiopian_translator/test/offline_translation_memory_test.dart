import 'package:flutter_test/flutter_test.dart';
import 'package:ethiopian_translator/offline_translation_memory.dart';

void main() {
  group('OfflineTranslationMemory Linguistic Processing Tests', () {
    test('Amharic homophone harmonization and orthographic normalization', () {
      // General normalize converts archaic homophones to canonical form
      expect(
        OfflineTranslationMemory.normalize('ሐኪም'),
        'ሀኪም',
      );
      expect(
        OfflineTranslationMemory.normalize('መድኃኒት'),
        'መድሀኒት',
      );
      // normalizeAmharic converts spoken colloquial forms to standard written forms
      expect(
        OfflineTranslationMemory.normalizeAmharic('እኔ ደናነኝ ኣንተ ደናነክ?'),
        'እኔ ደህና ነኝ አንተ ደህና ነህ?',
      );
    });

    test('Tigrinya normalization and punctuation cleaning', () {
      final normalized = OfflineTranslationMemory.normalizeTigrinya('ሰላም ፡ ከመይ ኣለኻ ።');
      expect(normalized, contains('ሰላም'));
      expect(normalized, contains('ከመይ ኣለኻ'));
    });

    test('Afaan Oromoo and Somali spelling normalization', () {
      expect(
        OfflineTranslationMemory.normalizeOromo("akam jirt"),
        'akkam jirta',
      );
      expect(
        OfflineTranslationMemory.normalizeSomali("waa aan"),
        'waan',
      );
    });

    test('Clean spoken transcription artifacts', () {
      expect(
        OfflineTranslationMemory.cleanSpokenTranscription('እኔ ደናነኝ ኣንተ ደናነክ?', 'amh'),
        'እኔ ደህና ነኝ አንተ ደህና ነህ?',
      );
      expect(
        OfflineTranslationMemory.cleanSpokenTranscription("i'm fine you're well", 'eng'),
        'I am fine you are well',
      );
    });

    test('Script and language detection heuristics', () {
      expect(
        OfflineTranslationMemory.detectLanguage('ሰላም እንዴት ነህ?'),
        'amh',
      );
      expect(
        OfflineTranslationMemory.detectLanguage('Akkam jirta? Nagaadhaa?'),
        'orm',
      );
      expect(
        OfflineTranslationMemory.detectLanguage('Sidee baad tahay saaxiib?'),
        'som',
      );
      expect(
        OfflineTranslationMemory.detectLanguage('Where is the nearest hospital?'),
        'eng',
      );
    });

    test('Levenshtein similarity calculation', () {
      expect(OfflineTranslationMemory.levenshteinSimilarity('hospital', 'hospital'), 1.0);
      expect(OfflineTranslationMemory.levenshteinSimilarity('hospital', 'hospitol') > 0.8, isTrue);
      expect(OfflineTranslationMemory.levenshteinSimilarity('abc', 'xyz'), 0.0);
    });

    test('Postprocessing anti-hallucination and formatting', () {
      expect(
        OfflineTranslationMemory.postprocess('I was rejected, and you were?', sourceLang: 'amh', targetLang: 'eng'),
        'I am fine, and you?',
      );
      expect(
        OfflineTranslationMemory.postprocess("I'm fine you are?", sourceLang: 'amh', targetLang: 'eng'),
        "I'm fine, how are you?",
      );
    });
  });
}
