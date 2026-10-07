import 'package:flutter_test/flutter_test.dart';
import 'package:ethiopian_translator/offline_translation_memory.dart';

void main() {
  group('OfflineTranslationMemory Tests', () {
    test('User reported sentence 0: እኔ ደናነኝ ኣንተ ደናነክ?', () {
      final eng = OfflineTranslationMemory.lookup(
        'እኔ ደናነኝ ኣንተ ደናነክ?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(eng, 'I am fine, and you?');

      final orm = OfflineTranslationMemory.lookup(
        'እኔ ደናነኝ ኣንተ ደናነክ?',
        sourceLang: 'amh',
        targetLang: 'orm',
      );
      expect(orm, 'Ani nagaadha, ati hoo nagaadhaa?');

      final tir = OfflineTranslationMemory.lookup(
        'እኔ ደናነኝ ኣንተ ደናነክ?',
        sourceLang: 'amh',
        targetLang: 'tir',
      );
      expect(tir, 'ኣነ ድሓን እየ፡ ንስኻኸ ድሓን ዲኻ?');

      final som = OfflineTranslationMemory.lookup(
        'እኔ ደናነኝ ኣንተ ደናነክ?',
        sourceLang: 'amh',
        targetLang: 'som',
      );
      expect(som, 'Anigu waan fiicanahay, adiguna ma fiican tahay?');

      // Test spoken variations
      expect(
        OfflineTranslationMemory.lookup('ደናነኝ አንተስ?', sourceLang: 'amh', targetLang: 'eng'),
        'I am fine, and you?',
      );
      expect(
        OfflineTranslationMemory.lookup('ደናነኝ', sourceLang: 'amh', targetLang: 'eng'),
        'I am fine.',
      );
      expect(
        OfflineTranslationMemory.lookup('ደናነክ?', sourceLang: 'amh', targetLang: 'eng'),
        'Are you doing well?',
      );

      // Test pre-normalization for NLLB
      expect(
        OfflineTranslationMemory.normalizeAmharic('እኔ ደናነኝ ኣንተ ደናነክ?'),
        'እኔ ደህና ነኝ አንተ ደህና ነህ?',
      );

      // Test postprocess anti-hallucination
      expect(
        OfflineTranslationMemory.postprocess('I was rejected, and you were?', sourceLang: 'amh', targetLang: 'eng'),
        'I am fine, and you?',
      );
      expect(
        OfflineTranslationMemory.postprocess("I'm fine you are?", sourceLang: 'amh', targetLang: 'eng'),
        "I'm fine, how are you?",
      );
    });

    test('User reported sentence 1: ምንህን ነው የሚያምህ?', () {
      final eng = OfflineTranslationMemory.lookup(
        'ምንህን ነው የሚያምህ?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(eng, 'Where does it hurt you?');

      final orm = OfflineTranslationMemory.lookup(
        'ምንህን ነው የሚያምህ?',
        sourceLang: 'amh',
        targetLang: 'orm',
      );
      expect(orm, 'Bakka kamtu si dhukkuba?');
    });

    test('User reported sentence 2: መድሃኒት አዝልሃለው', () {
      final eng = OfflineTranslationMemory.lookup(
        'መድሃኒት አዝልሃለው',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(eng, 'I will prescribe you medicine.');

      final orm = OfflineTranslationMemory.lookup(
        'መድሃኒት አዝልሃለው',
        sourceLang: 'amh',
        targetLang: 'orm',
      );
      expect(orm, 'Qoricha siif ajaja.');
    });

    test('User reported sentence 3: ሰላም እንዴት ነህ?', () {
      final orm = OfflineTranslationMemory.lookup(
        'ሰላም እንዴት ነህ?',
        sourceLang: 'amh',
        targetLang: 'orm',
      );
      expect(orm, 'Akkam jirta?');

      final eng = OfflineTranslationMemory.lookup(
        'ሰላም እንዴት ነህ?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(eng, 'Hello, how are you?');
    });

    test('Homophone tolerance: መድሃኒት vs መድኃኒት', () {
      final eng1 = OfflineTranslationMemory.lookup(
        'መድኃኒት አዝልሃለሁ',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(eng1, 'I will prescribe you medicine.');
    });

    test('Clinic scenario sentence from corpus', () {
      final eng = OfflineTranslationMemory.lookup(
        'የት አካባቢ ያመዎታል፣ መቼ ነው የጀመረው?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(eng, 'Where does it hurt, and when did it start?');
    });

    test('Particle stripping: prefix and suffix tolerance', () {
      final eng1 = OfflineTranslationMemory.lookup(
        'እባክህ ምንህን ነው የሚያምህ?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(eng1, 'Where does it hurt you?');

      final eng2 = OfflineTranslationMemory.lookup(
        'ምንህን ነው የሚያምህ ወንድሜ?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(eng2, 'Where does it hurt you?');

      final orm = OfflineTranslationMemory.lookup(
        'ሰላም ወንድሜ እንዴት ነህ?',
        sourceLang: 'amh',
        targetLang: 'orm',
      );
      expect(orm, 'Akkam jirta?');
    });

    test('Semantic intents: headache, fever, stomach ache', () {
      final head = OfflineTranslationMemory.lookup(
        'በጣም ራሴን ያመኛል',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(head, 'I have a headache.');

      final stomach = OfflineTranslationMemory.lookup(
        'ሆዴን ያመኛል',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(stomach, 'I have a stomach ache.');

      final fever = OfflineTranslationMemory.lookup(
        'ከፍተኛ ትኩሳት አለብኝ',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(fever, 'I have a high fever.');
    });

    test('Reverse lookup: English to Amharic and Oromo', () {
      final amh = OfflineTranslationMemory.lookup(
        'Where does it hurt you?',
        sourceLang: 'eng',
        targetLang: 'amh',
      );
      expect(amh, isNotNull);

      final orm = OfflineTranslationMemory.lookup(
        'I will prescribe you medicine.',
        sourceLang: 'eng',
        targetLang: 'orm',
      );
      expect(orm, 'Qoricha siif ajaja.');
    });

    test('Post-processing deduplication removes repetition loops', () {
      final deduped = OfflineTranslationMemory.postprocess(
        'Salaam, salaam, salaam',
        sourceLang: 'amh',
        targetLang: 'orm',
      );
      expect(deduped, 'Akkam');
    });

    test('Cross-Language: Afaan Oromo source translations', () {
      // Greetings
      expect(
        OfflineTranslationMemory.lookup('Akkam jirta?', sourceLang: 'orm', targetLang: 'eng'),
        'Hello, how are you?',
      );
      expect(
        OfflineTranslationMemory.lookup('Akkam jirta?', sourceLang: 'orm', targetLang: 'amh'),
        'ሰላም፣ እንዴት ነህ?',
      );
      expect(
        OfflineTranslationMemory.lookup('Akkam jirta?', sourceLang: 'orm', targetLang: 'tir'),
        'ሰላም ከመይ ኣለኻ?',
      );
      expect(
        OfflineTranslationMemory.lookup('Akkam jirta?', sourceLang: 'orm', targetLang: 'som'),
        'Sidee tahay?',
      );

      // Conversational fine exchange
      expect(
        OfflineTranslationMemory.lookup('Ani nagaadha, ati hoo?', sourceLang: 'orm', targetLang: 'eng'),
        'I am fine, and you?',
      );
      expect(
        OfflineTranslationMemory.lookup('Ani nagaadha, ati hoo?', sourceLang: 'orm', targetLang: 'amh'),
        'እኔ ደህና ነኝ፣ አንተስ?',
      );
      expect(
        OfflineTranslationMemory.lookup('Ani nagaadha, ati hoo?', sourceLang: 'orm', targetLang: 'tir'),
        'ኣነ ድሓን እየ፡ ንስኻኸ ድሓን ዲኻ?',
      );
      expect(
        OfflineTranslationMemory.lookup('Ani nagaadha, ati hoo?', sourceLang: 'orm', targetLang: 'som'),
        'Anigu waan fiicanahay, adiguna ma fiican tahay?',
      );

      // Hudhaa / glottal stop preservation in fever intent
      expect(
        OfflineTranslationMemory.lookup("Ho'a qaamaa qaba.", sourceLang: 'orm', targetLang: 'eng'),
        'I have a high fever.',
      );
      expect(
        OfflineTranslationMemory.lookup("Ho'a qaamaa qaba", sourceLang: 'orm', targetLang: 'tir'),
        'ሓያል ረስኒ ኣሎኒ።',
      );
    });

    test('Cross-Language: Tigrinya source translations', () {
      // Greetings
      expect(
        OfflineTranslationMemory.lookup('ሰላም ከመይ ኣለኻ?', sourceLang: 'tir', targetLang: 'eng'),
        'Hello, how are you?',
      );
      expect(
        OfflineTranslationMemory.lookup('ሰላም ከመይ ኣለኻ?', sourceLang: 'tir', targetLang: 'amh'),
        'ሰላም፣ እንዴት ነህ?',
      );
      expect(
        OfflineTranslationMemory.lookup('ሰላም ከመይ ኣለኻ?', sourceLang: 'tir', targetLang: 'orm'),
        'Akkam jirta?',
      );
      expect(
        OfflineTranslationMemory.lookup('ሰላም ከመይ ኣለኻ?', sourceLang: 'tir', targetLang: 'som'),
        'Sidee tahay?',
      );

      // Conversational fine exchange with Ge'ez word separator
      expect(
        OfflineTranslationMemory.lookup('ኣነ ድሓን እየ፡ ንስኻኸ?', sourceLang: 'tir', targetLang: 'eng'),
        'I am fine, and you?',
      );
      expect(
        OfflineTranslationMemory.lookup('ኣነ ድሓን እየ፡ ንስኻኸ?', sourceLang: 'tir', targetLang: 'amh'),
        'እኔ ደህና ነኝ፣ አንተስ?',
      );
      expect(
        OfflineTranslationMemory.lookup('ኣነ ድሓን እየ፡ ንስኻኸ?', sourceLang: 'tir', targetLang: 'orm'),
        'Ani nagaadha, ati hoo nagaadhaa?',
      );
      expect(
        OfflineTranslationMemory.lookup('ኣነ ድሓን እየ፡ ንስኻኸ?', sourceLang: 'tir', targetLang: 'som'),
        'Anigu waan fiicanahay, adiguna ma fiican tahay?',
      );

      // Normalization of Ge'ez separator colon
      expect(
        OfflineTranslationMemory.normalizeTigrinya('ኣነ ድሓን እየ፡ ንስኻኸ?'),
        'ኣነ ድሓን እየ ንስኻኸ?',
      );
    });

    test('Cross-Language: Somali source translations', () {
      // Greetings
      expect(
        OfflineTranslationMemory.lookup('Sidee tahay?', sourceLang: 'som', targetLang: 'eng'),
        'Hello, how are you?',
      );
      expect(
        OfflineTranslationMemory.lookup('Sidee tahay?', sourceLang: 'som', targetLang: 'amh'),
        'ሰላም፣ እንዴት ነህ?',
      );
      expect(
        OfflineTranslationMemory.lookup('Sidee tahay?', sourceLang: 'som', targetLang: 'orm'),
        'Akkam jirta?',
      );
      expect(
        OfflineTranslationMemory.lookup('Sidee tahay?', sourceLang: 'som', targetLang: 'tir'),
        'ሰላም ከመይ ኣለኻ?',
      );

      // Conversational fine exchange
      expect(
        OfflineTranslationMemory.lookup('Waan fiicanahay, adiguna?', sourceLang: 'som', targetLang: 'eng'),
        'I am fine, and you?',
      );
      expect(
        OfflineTranslationMemory.lookup('Waan fiicanahay, adiguna?', sourceLang: 'som', targetLang: 'amh'),
        'እኔ ደህና ነኝ፣ አንተስ?',
      );
      expect(
        OfflineTranslationMemory.lookup('Waan fiicanahay, adiguna?', sourceLang: 'som', targetLang: 'orm'),
        'Ani nagaadha, ati hoo nagaadhaa?',
      );
      expect(
        OfflineTranslationMemory.lookup('Waan fiicanahay, adiguna?', sourceLang: 'som', targetLang: 'tir'),
        'ኣነ ድሓን እየ፡ ንስኻኸ ድሓን ዲኻ?',
      );

      // Contraction normalization
      expect(
        OfflineTranslationMemory.normalizeSomali('waa aan ladnahay baa aan ahay'),
        'waan ladnahay baan ahay',
      );
    });

    test('Cross-Language: English source translations to all 4 languages', () {
      expect(
        OfflineTranslationMemory.lookup('Hello, how are you?', sourceLang: 'eng', targetLang: 'amh'),
        'ሰላም፣ እንዴት ነህ?',
      );
      expect(
        OfflineTranslationMemory.lookup('Hello, how are you?', sourceLang: 'eng', targetLang: 'orm'),
        'Akkam jirta?',
      );
      expect(
        OfflineTranslationMemory.lookup('Hello, how are you?', sourceLang: 'eng', targetLang: 'tir'),
        'ሰላም ከመይ ኣለኻ?',
      );
      expect(
        OfflineTranslationMemory.lookup('Hello, how are you?', sourceLang: 'eng', targetLang: 'som'),
        'Sidee tahay?',
      );

      // English Contraction handling
      expect(
        OfflineTranslationMemory.lookup("I'm fine, and you?", sourceLang: 'eng', targetLang: 'amh'),
        'እኔ ደህና ነኝ፣ አንተስ?',
      );
      expect(
        OfflineTranslationMemory.normalizeEnglish("i'm you're what's where's don't can't"),
        'I am you are what is where is do not cannot',
      );
    });

    test('Cross-Language Anti-Hallucination filters for all 5 languages', () {
      // English target
      expect(
        OfflineTranslationMemory.postprocess('what is your religion?', sourceLang: 'amh', targetLang: 'eng'),
        'Where does it hurt you?',
      );
      expect(
        OfflineTranslationMemory.postprocess('he was a good doctor.', sourceLang: 'amh', targetLang: 'eng'),
        'I will prescribe you medicine.',
      );

      // Afaan Oromo target
      expect(
        OfflineTranslationMemory.postprocess('amantiin kee maali?', sourceLang: 'amh', targetLang: 'orm'),
        'Bakka kamtu si dhukkuba?',
      );
      expect(
        OfflineTranslationMemory.postprocess('doktora gaarii ture.', sourceLang: 'amh', targetLang: 'orm'),
        'Qoricha siif ajaja.',
      );

      // Tigrinya target
      expect(
        OfflineTranslationMemory.postprocess('እምነትካ እንታይ እዩ?', sourceLang: 'amh', targetLang: 'tir'),
        'ኣበይ የሕምመካ ኣሎ?',
      );
      expect(
        OfflineTranslationMemory.postprocess('ጽቡቕ ሓኪም ነይሩ', sourceLang: 'amh', targetLang: 'tir'),
        'መድሃኒት ክእዝዘልካ እየ።',
      );

      // Somali target
      expect(
        OfflineTranslationMemory.postprocess('diintaadu waa maxay?', sourceLang: 'amh', targetLang: 'som'),
        'Xaggee ku xanuunaysaa?',
      );
      expect(
        OfflineTranslationMemory.postprocess('dhakhtar fiican buu ahaa.', sourceLang: 'amh', targetLang: 'som'),
        'Daawaan kuu qorayaa.',
      );

      // Amharic target
      expect(
        OfflineTranslationMemory.postprocess('እምነትህ ምንድን ነው?', sourceLang: 'orm', targetLang: 'amh'),
        'የት አካባቢ ያመዎታል?',
      );
      expect(
        OfflineTranslationMemory.postprocess('ጥሩ ዶክተር ነበር', sourceLang: 'orm', targetLang: 'amh'),
        'መድኃኒት አዝልሃለሁ።',
      );
    });

    test('normalizeForNmt delegates properly for all 5 languages', () {
      expect(OfflineTranslationMemory.normalizeForNmt('ደናነኝ', 'amh'), 'ደህና ነኝ');
      expect(OfflineTranslationMemory.normalizeForNmt('ሰላም፡ከመይ', 'tir'), 'ሰላም ከመይ');
      expect(OfflineTranslationMemory.normalizeForNmt("  ho'a  ", 'orm'), "ho'a");
      expect(OfflineTranslationMemory.normalizeForNmt('waa aan tagay', 'som'), 'waan tagay');
      expect(OfflineTranslationMemory.normalizeForNmt("don't go", 'eng'), 'do not go');
    });

    test('User reported speech issue: ሰለም እንዴት ነ ደናነ?', () {
      // 1. Acoustic / STT normalizer restores dropped phonemes and trailing aspirates
      final cleaned = OfflineTranslationMemory.cleanSpokenTranscription('ሰለም እንዴት ነ ደናነ?', 'amh');
      expect(cleaned, 'ሰላም እንዴት ነህ ደህና ነህ?');

      // 2. High-speed Translation Memory lookup directly resolves the degraded input
      final engFromDegraded = OfflineTranslationMemory.lookup(
        'ሰለም እንዴት ነ ደናነ?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(engFromDegraded, 'Hello, how are you? Are you doing well?');

      // 3. User spoken variant: ሰላም እንዴት ነህ ደና ነህ?
      final engFromSpoken = OfflineTranslationMemory.lookup(
        'ሰላም እንዴት ነህ ደና ነህ?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(engFromSpoken, 'Hello, how are you? Are you doing well?');

      // 4. Cross-language compound greeting outputs
      expect(
        OfflineTranslationMemory.lookup('ሰለም እንዴት ነ ደናነ?', sourceLang: 'amh', targetLang: 'orm'),
        'Akkam jirta, nagaa qabdaa?',
      );
      expect(
        OfflineTranslationMemory.lookup('ሰለም እንዴት ነ ደናነ?', sourceLang: 'amh', targetLang: 'tir'),
        'ሰላም ከመይ ኣለኻ፡ ድሓን ዲኻ?',
      );
      expect(
        OfflineTranslationMemory.lookup('ሰለም እንዴት ነ ደናነ?', sourceLang: 'amh', targetLang: 'som'),
        'Sidee tahay, ma fiican tahay?',
      );

      // 5. Anti-hallucination filter catches "how did the painting end"
      final fixedHallucination = OfflineTranslationMemory.postprocess(
        'how did the painting end?',
        sourceLang: 'amh',
        targetLang: 'eng',
      );
      expect(fixedHallucination, 'Hello, how are you? Are you doing well?');
    });

    test('Cross-Language speech normalizer and compound greeting resolution', () {
      // Afaan Oromo speech restoration & compound greeting
      final ormClean = OfflineTranslationMemory.cleanSpokenTranscription('akam jirt naga qabda', 'orm');
      expect(ormClean.contains('akkam') && ormClean.contains('nagaa'), isTrue);

      final ormToEng = OfflineTranslationMemory.lookup(
        'Akkam jirta, nagaa qabdaa?',
        sourceLang: 'orm',
        targetLang: 'eng',
      );
      expect(ormToEng, 'Hello, how are you? Are you doing well?');

      final ormToAmh = OfflineTranslationMemory.lookup(
        'Akkam jirta, nagaa qabdaa?',
        sourceLang: 'orm',
        targetLang: 'amh',
      );
      expect(ormToAmh, 'ሰላም፣ እንዴት ነህ? ደህና ነህ?');

      // Tigrinya speech restoration & compound greeting
      final tirClean = OfflineTranslationMemory.cleanSpokenTranscription('ከመይ ኣለ ድሓን ዲ', 'tir');
      expect(tirClean, 'ከመይ ኣለኻ ድሓን ዲኻ');

      final tirToEng = OfflineTranslationMemory.lookup(
        'ሰላም ከመይ ኣለኻ፡ ድሓን ዲኻ?',
        sourceLang: 'tir',
        targetLang: 'eng',
      );
      expect(tirToEng, 'Hello, how are you? Are you doing well?');

      final tirToAmh = OfflineTranslationMemory.lookup(
        'ሰላም ከመይ ኣለኻ፡ ድሓን ዲኻ?',
        sourceLang: 'tir',
        targetLang: 'amh',
      );
      expect(tirToAmh, 'ሰላም፣ እንዴት ነህ? ደህና ነህ?');

      // Somali speech restoration & compound greeting
      final somClean = OfflineTranslationMemory.cleanSpokenTranscription('side tahy ma fiican tahy', 'som');
      expect(somClean, 'sidee tahay ma fiican tahay');

      final somToEng = OfflineTranslationMemory.lookup(
        'Sidee tahay, ma fiican tahay?',
        sourceLang: 'som',
        targetLang: 'eng',
      );
      expect(somToEng, 'Hello, how are you? Are you doing well?');

      final somToAmh = OfflineTranslationMemory.lookup(
        'Sidee tahay, ma fiican tahay?',
        sourceLang: 'som',
        targetLang: 'amh',
      );
      expect(somToAmh, 'ሰላም፣ እንዴት ነህ? ደህና ነህ?');

      // English compound greeting to Ethiopian languages
      expect(
        OfflineTranslationMemory.lookup(
          'Hello, how are you? Are you doing well?',
          sourceLang: 'eng',
          targetLang: 'amh',
        ),
        'ሰላም፣ እንዴት ነህ? ደህና ነህ?',
      );
      expect(
        OfflineTranslationMemory.lookup(
          'Hello, how are you? Are you doing well?',
          sourceLang: 'eng',
          targetLang: 'orm',
        ),
        'Akkam jirta, nagaa qabdaa?',
      );
      expect(
        OfflineTranslationMemory.lookup(
          'Hello, how are you? Are you doing well?',
          sourceLang: 'eng',
          targetLang: 'tir',
        ),
        'ሰላም ከመይ ኣለኻ፡ ድሓን ዲኻ?',
      );
      expect(
        OfflineTranslationMemory.lookup(
          'Hello, how are you? Are you doing well?',
          sourceLang: 'eng',
          targetLang: 'som',
        ),
        'Sidee tahay, ma fiican tahay?',
      );
    });

    test('detectLanguage automatically recognises all 5 Ethiopian languages', () {
      // 1. Amharic sentences
      expect(OfflineTranslationMemory.detectLanguage('እኔ ደህና ነኝ አንተ ደህና ነህ?'), 'amh');
      expect(OfflineTranslationMemory.detectLanguage('ምንህን ነው የሚያምህ?'), 'amh');
      expect(OfflineTranslationMemory.detectLanguage('መድሃኒት አዝልሃለው'), 'amh');
      expect(OfflineTranslationMemory.detectLanguage('ሰላም አመሰግናለሁ'), 'amh');

      // 2. Tigrinya sentences
      expect(OfflineTranslationMemory.detectLanguage('ከመይ ኣለኻ ሓወይ?'), 'tir');
      expect(OfflineTranslationMemory.detectLanguage('ጽቡቕ ኣለኹ የቐንየለይ'), 'tir');
      expect(OfflineTranslationMemory.detectLanguage('ጥዕና ይሃበለይ እንታይ ትደሊ ኣለኻ?'), 'tir');

      // 3. Afaan Oromoo sentences
      expect(OfflineTranslationMemory.detectLanguage('Akkam jirta, nagaa dhaa?'), 'orm');
      expect(OfflineTranslationMemory.detectLanguage('Maal barbaadda? Galatoomi'), 'orm');
      expect(OfflineTranslationMemory.detectLanguage('Bishaan barbaada'), 'orm');

      // 4. Somali sentences
      expect(OfflineTranslationMemory.detectLanguage('Sidee tahay, ma fiican tahay?'), 'som');
      expect(OfflineTranslationMemory.detectLanguage('Subax wanaagsan mahadsanid'), 'som');
      expect(OfflineTranslationMemory.detectLanguage('Waan fiicanahay adigu sidee tahay?'), 'som');

      // 5. English sentences
      expect(OfflineTranslationMemory.detectLanguage('Hello doctor, where does it hurt?'), 'eng');
      expect(OfflineTranslationMemory.detectLanguage('I have a severe headache and fever'), 'eng');
      expect(OfflineTranslationMemory.detectLanguage('Thank you very much for your help'), 'eng');

      // 6. Explicit STT model tokens
      expect(OfflineTranslationMemory.detectLanguage('[AMH] ሰላም'), 'amh');
      expect(OfflineTranslationMemory.detectLanguage('[ORM] akkam'), 'orm');
      expect(OfflineTranslationMemory.detectLanguage('[TIR] ከመይ'), 'tir');
      expect(OfflineTranslationMemory.detectLanguage('[SOM] nabad'), 'som');
      expect(OfflineTranslationMemory.detectLanguage('[ENG] hello'), 'eng');
    });
  });
}
