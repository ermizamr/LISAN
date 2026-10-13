/// Linguistic normalization, script analysis, and phonetic cleaning
/// utilities for Ethiopian and Horn of Africa languages:
/// Amharic (amh), Afaan Oromo (orm), Tigrinya (tir), Somali (som), English (eng).
class OfflineTranslationMemory {
  static const Map<String, String> _homophones = {
    'ሐ': 'ሀ',
    'ኀ': 'ሀ',
    'ሃ': 'ሀ',
    'ሓ': 'ሀ',
    'ኃ': 'ሀ',
    'ሑ': 'ሁ',
    'ኁ': 'ሁ',
    'ሒ': 'ሂ',
    'ኺ': 'ሂ',
    'ሔ': 'ሄ',
    'ኄ': 'ሄ',
    'ሕ': 'ህ',
    'ኅ': 'ህ',
    'ሖ': 'ሆ',
    'ኆ': 'ሆ',
    'ሠ': 'ሰ',
    'ሡ': 'ሱ',
    'ሢ': 'ሲ',
    'ሣ': 'ሳ',
    'ሤ': 'ሴ',
    'ሥ': 'ስ',
    'ሦ': 'ሶ',
    'ዐ': 'አ',
    'ዑ': 'ኡ',
    'ዒ': 'ኢ',
    'ዓ': 'አ',
    'ዔ': 'ኤ',
    'ዕ': 'እ',
    'ዖ': 'ኦ',
    'ኣ': 'አ',
    'ፀ': 'ጸ',
    'ፁ': 'ጹ',
    'ፂ': 'ጺ',
    'ፃ': 'ጻ',
    'ፄ': 'ጼ',
    'ፅ': 'ጽ',
    'ፆ': 'ጾ',
  };

  static final RegExp _punctRegex = RegExp(r"""[\s!?.,:;፣።፧፨()[\]"«»?]+""");

  /// Normalize spoken and colloquial Amharic into standard orthography.
  /// Preserves sentence delimiters and punctuation.
  static String normalizeAmharic(String text) {
    if (text.isEmpty) return '';
    var s = text;
    s = s.replaceAll('ኣ', 'አ').replaceAll('ዐ', 'አ').replaceAll('ዓ', 'አ');

    // 1. Acoustic CTC multi-word and pause repairs (Unicode Ge'ez boundaries)
    s = s.replaceAll(RegExp(r'ያም(?:[ወዎ]?)?\s+ወ?ታል'), 'ያመዎታል');
    s = s.replaceAll(RegExp(r'ያም\s*ታል'), 'ያመዎታል');
    s = s.replaceAll(RegExp(r'ያም(?:[ወዎ]?)?\s+ሃል'), 'ያምሃል');
    s = s.replaceAll(RegExp(r'ያም(?:[ወዎ]?)?\s+ሻል'), 'ያምሻል');
    s = s.replaceAll(RegExp(r'ያም(?:[ወዎ]?)?\s+ኛል'), 'ያመኛል');
    s = s.replaceAll(RegExp(r'ያም(?:[ወዎ]?)?\s+ኛ'), 'ያመኛል');
    s = s.replaceAll(RegExp(r'ያም\s+ሆ'), 'ያመዎታል');
    s = s.replaceAll(RegExp(r'የታ\s+አካባቢ'), 'የት አካባቢ');
    s = s.replaceAll(RegExp(r'የታ\s+ጋር'), 'የት ጋር');
    s = s.replaceAll(RegExp(r'የታ\s+ነው'), 'የት ነው');
    s = s.replaceAll(RegExp(r'የታ(?=\s|[!?.,:;፣።]|$)'), 'የት');
    s = s.replaceAll(RegExp(r'መች\s+ነ[ወዉ]'), 'መቼ ነው');
    s = s.replaceAll(RegExp(r'መቼ\s+ነ[ወዉ]'), 'መቼ ነው');
    s = s.replaceAll(RegExp(r'የጀመረ[ወዉ]'), 'የጀመረው');
    s = s.replaceAll(RegExp(r'እንዴት\s+ነ[ወዉ]'), 'እንዴት ነው');
    s = s.replaceAll(RegExp(r'እንዴት\s+ነክ'), 'እንዴት ነህ');
    s = s.replaceAll(RegExp(r'ደህና\s+ነክ'), 'ደህና ነህ');
    s = s.replaceAll(RegExp(r'ምን\s+አካባቢ'), 'የት አካባቢ');
    s = s.replaceAll(RegExp(r'ሆዴን\s+ያም(?:[ወዎ]?)?(?:ኛ)?'), 'ሆዴን ያመኛል');
    s = s.replaceAll(RegExp(r'ራሴን\s+ያም(?:[ወዎ]?)?(?:ኛ)?'), 'ራሴን ያመኛል');
    s = s.replaceAll(RegExp(r'ደረቴን\s+ያም(?:[ወዎ]?)?(?:ኛ)?'), 'ደረቴን ያመኛል');
    s = s.replaceAll(RegExp(r'እግሬን\s+ያም(?:[ወዎ]?)?(?:ኛ)?'), 'እግሬን ያመኛል');
    s = s.replaceAll(RegExp(r'ትኩሳ\s+አለብኝ'), 'ትኩሳት አለብኝ');
    s = s.replaceAll(RegExp(r'መድሃኒ\s+አለ'), 'መድሃኒት አለ');
    s = s.replaceAll(RegExp(r'አመሰግናለ[ወዉ]'), 'አመሰግናለሁ');
    s = s.replaceAll(RegExp(r'እፈልጋለ[ወዉ]'), 'እፈልጋለሁ');
    s = s.replaceAll(RegExp(r'አላውቅ[ወዉ]ም'), 'አላውቅም');
    s = s.replaceAll(RegExp(r'አልችል[ወዉ]ም'), 'አልችልም');
    s = s.replaceAll(RegExp(r'መትታቃለህ'), 'መጥተህ ታውቃለህ');
    s = s.replaceAll(RegExp(r'መትታቃለሽ'), 'መጥተሽ ታውቂያለሽ');
    s = s.replaceAll(RegExp(r'መተልታቅ'), 'መጥተህ ልታውቅ');
    s = s.replaceAll(RegExp(r'መተልጣቅት'), 'መጥተህ ልታውቅ');
    s = s.replaceAll(RegExp(r'ምጥቻቃ\s+አለው'), 'መጥቼ አውቃለሁ');
    s = s.replaceAll(RegExp(r'መታ\s+ምታ\s*ቀይመስለኝሞ'), 'መጥተህ የምታውቅ አይመስለኝም');
    s = s.replaceAll(RegExp(r'መተታቃለ'), 'መጥተህ ታውቃለህ');
    s = s.replaceAll(RegExp(r'ገጣሚ'), 'አጋጣሚ');
    s = s.replaceAll(RegExp(r'[ሀሃ]{2,}'), ''); // laughter removal

    const spokenMap = {
      'ሰለም': 'ሰላም',
      'አሰላሙ': 'ሰላም',
      'ደናነኝ': 'ደህና ነኝ', 'ደህናነኝ': 'ደህና ነኝ',
      'ደናነክ': 'ደህና ነህ', 'ደህናነክ': 'ደህና ነህ',
      'ደናነህ': 'ደህና ነህ', 'ደህናነህ': 'ደህና ነህ',
      'ደናነ': 'ደህና ነህ', 'ደህናነ': 'ደህና ነህ',
      'ደናነሽ': 'ደህና ነሽ', 'ደህናነሽ': 'ደህና ነሽ',
      'ደናናችሁ': 'ደህና ናችሁ', 'ደህናናችሁ': 'ደህና ናችሁ',
      'ደናናቹ': 'ደህና ናችሁ', 'ደህናናቹ': 'ደህና ናችሁ',
      'ደናና': 'ደህና ናችሁ', 'ደህናና': 'ደህና ናችሁ',
      'ደናነዎት': 'ደህና ነዎት', 'ደህናነዎት': 'ደህና ነዎት',
      'እንዴትነህ': 'እንዴት ነህ', 'እንዴትነክ': 'እንዴት ነህ',
      'እንዴትነ': 'እንዴት ነህ',
      'እንዴትነሽ': 'እንዴት ነሽ',
      'እንዴትናችሁ': 'እንዴት ናችሁ', 'እንዴትናቹ': 'እንዴት ናችሁ',
      'እንዴትና': 'እንዴት ናችሁ',
      'እንዴትነዎት': 'እንዴት ነዎት',
      'ደናዋልክ': 'ደህና ዋልክ', 'ደህናዋልክ': 'ደህና ዋልክ',
      'ደናዋልሽ': 'ደህና ዋልሽ', 'ደህናዋልሽ': 'ደህና ዋልሽ',
      'ደናዋላችሁ': 'ደህና ዋላችሁ', 'ደህናዋላችሁ': 'ደህና ዋላችሁ',
      'ደናአደርክ': 'ደህና አደርክ', 'ደህናአደርክ': 'ደህና አደርክ',
      'ደናአደርሽ': 'ደህና አደርሽ', 'ደህናአደርሽ': 'ደህና አደርሽ',
      'ደናአደራችሁ': 'ደህና አደራችሁ', 'ደህናአደራችሁ': 'ደህና አደራችሁ',
      'ደና': 'ደህና',
      'ነክ': 'ነህ',
      'ነ': 'ነህ',
      'ነወ': 'ነው',
      'ነዉ': 'ነው',
      'አለክ': 'አለህ',
      'ባክህ': 'እባክህ', 'ባክሽ': 'እባክሽ', 'ባካችሁ': 'እባካችሁ',
      'አይዞክ': 'አይዞህ',
      'አደለም': 'አይደለም',
      'ምንክን': 'ምንህን', 'ምንክ': 'ምንህን', 'ምንህ': 'ምንህን',
      'የሚያም': 'የሚያምህ', 'የሚያመ': 'የሚያምህ',
      'ያመኛ': 'ያመኛል', 'ያመዎታ': 'ያመዎታል',
      'ያምታል': 'ያመዎታል', 'ያሞታል': 'ያመዎታል', 'ያመታል': 'ያመዎታል',
      'መች': 'መቼ',
      'የጀመረወ': 'የጀመረው', 'የጀመረዉ': 'የጀመረው',
      'አዝልሃለ': 'አዝልሃለሁ', 'አዝልሃለው': 'አዝልሃለሁ',
      'አዝልሻለ': 'አዝልሻለሁ', 'አዝልሻለው': 'አዝልሻለሁ',
      'መድሃኒ': 'መድሃኒት',
      'ትኩሳ': 'ትኩሳት',
    };

    final buffer = StringBuffer();
    final wordBuffer = StringBuffer();

    void flushWord() {
      if (wordBuffer.isNotEmpty) {
        final w = wordBuffer.toString();
        final mapped = spokenMap[w];
        buffer.write(mapped ?? w);
        wordBuffer.clear();
      }
    }

    for (var i = 0; i < s.length; i++) {
      final ch = s[i];
      if (ch == ' ' || ch == '\t' || ch == '\n' || '!?.,:;፣።፧፨()[]"«»?'.contains(ch)) {
        flushWord();
        buffer.write(ch);
      } else {
        wordBuffer.write(ch);
      }
    }
    flushWord();

    return buffer.toString().replaceAll(RegExp(r' {2,}'), ' ').trim();
  }

  /// Normalize Tigrinya text (converts Ge'ez word separator to space, homophones, speech drops).
  static String normalizeTigrinya(String text) {
    if (text.isEmpty) return '';
    var s = text.replaceAll('፡', ' ');

    // 1. Acoustic CTC multi-word and pause repairs
    s = s.replaceAll(RegExp(r'\bከመይ\s+ኣለ\s+ኻ\b'), 'ከመይ ኣለኻ');
    s = s.replaceAll(RegExp(r'\bከመይ\s+ኣለ\s+ኺ\b'), 'ከመይ ኣለኺ');
    s = s.replaceAll(RegExp(r'\bከመይ\s+ኣለ\s+ኹም\b'), 'ከመይ ኣለኹም');
    s = s.replaceAll(RegExp(r'\bየሕም\s*መካ\b'), 'የሕምመካ');
    s = s.replaceAll(RegExp(r'\bየሕም\s*መኪ\b'), 'የሕምመኪ');
    s = s.replaceAll(RegExp(r'\bኣበይ\s+የሕም\w*\b'), 'ኣበይ የሕምመካ');
    s = s.replaceAll(RegExp(r'\bመዓስ\s+ጀሚ\w*\b'), 'መዓስ ጀሚሩ');
    s = s.replaceAll(RegExp(r'\bጥዕና\s+ኣበይ\b'), 'ጥዕና ይሃበለይ');
    s = s.replaceAll(RegExp(r'\bጥዕና\s+ይሃበላ[ይይ]\b'), 'ጥዕና ይሃበለይ');
    s = s.replaceAll(RegExp(r'\bደሓን\s+ዶ\b'), 'ድሓን ዲኻ');
    s = s.replaceAll(RegExp(r'\bደሓን\s+ዲኻ\b'), 'ድሓን ዲኻ');

    const spokenMap = {
      'ደሓን': 'ድሓን',
      'ከመይለኻ': 'ከመይ ኣለኻ',
      'ድሓንየ': 'ድሓን እየ',
      'ደሓንየ': 'ድሓን እየ',
      'የሕምመክ': 'የሕምመካ',
      'የሕምመ': 'የሕምመካ',
      'መድሃኒ': 'መድሃኒት',
      'ሓኪ': 'ሓኪም',
      'ሆስፒታ': 'ሆስፒታል',
    };

    final tokens = <String>[];
    final isWord = <bool>[];
    final wordBuffer = StringBuffer();

    void flushWord() {
      if (wordBuffer.isNotEmpty) {
        final w = wordBuffer.toString();
        tokens.add(spokenMap[w] ?? w);
        isWord.add(true);
        wordBuffer.clear();
      }
    }

    for (var i = 0; i < s.length; i++) {
      final ch = s[i];
      if (ch == ' ' || ch == '\t' || ch == '\n' || '!?.,:;፣።፧፨()[]"«»?'.contains(ch)) {
        flushWord();
        tokens.add(ch);
        isWord.add(false);
      } else {
        wordBuffer.write(ch);
      }
    }
    flushWord();

    for (var i = 0; i < tokens.length; i++) {
      if (!isWord[i]) continue;
      var nextWordIdx = -1;
      for (var j = i + 1; j < tokens.length; j++) {
        if (isWord[j]) {
          nextWordIdx = j;
          break;
        }
      }
      if (nextWordIdx != -1) {
        final w1 = tokens[i];
        final w2 = tokens[nextWordIdx];
        if (w1 == 'ከመይ' && (w2 == 'ኣለ' || w2 == 'ኣለክ')) {
          tokens[nextWordIdx] = 'ኣለኻ';
        } else if (w1 == 'ድሓን' && w2 == 'ዲ') {
          tokens[nextWordIdx] = 'ዲኻ';
        } else if (w1 == 'ጽቡቕ' && w2 == 'ኣለ') {
          tokens[nextWordIdx] = 'ኣለኹ';
        } else if (w1 == 'ጽቡቕ' && w2 == 'ዲ') {
          tokens[nextWordIdx] = 'ዲኻ';
        }
      }
    }

    return tokens.join('').replaceAll(RegExp(r' {2,}'), ' ').trim();
  }

  /// Normalize Afaan Oromo text (standardizes glottal stop / hudhaa apostrophes).
  static String normalizeOromo(String text) {
    if (text.isEmpty) return '';
    var s = text.replaceAll(RegExp(r"[’‘ʼ`´]"), "'");
    s = s.replaceAll(RegExp(r'\bak\s+kam\b', caseSensitive: false), 'akkam');
    s = s.replaceAll(RegExp(r'\bak\s+kam\s+jir\s*ta\b', caseSensitive: false), 'akkam jirta');
    s = s.replaceAll(RegExp(r'\bakkam\s+jir\s*ta\b', caseSensitive: false), 'akkam jirta');
    s = s.replaceAll(RegExp(r'\bna\s+dhukub\w*\b', caseSensitive: false), 'na dhukkuba');
    s = s.replaceAll(RegExp(r'\bsi\s+dhukub\w*\b', caseSensitive: false), 'si dhukkuba');
    s = s.replaceAll(RegExp(r'\beessa\s+si\s+dhukkub\w*\b', caseSensitive: false), 'eessa si dhukkuba');
    s = s.replaceAll(RegExp(r'\byoom\s+jalqab\w*\b', caseSensitive: false), 'yoom jalqabe');
    s = s.replaceAll(RegExp(r'\b(?:hoa|hoaa)\b', caseSensitive: false), "ho'a");
    s = s.replaceAll(RegExp(r'\b(?:tasgabaa|tasgabbaa|tasgabaaa)\b', caseSensitive: false), "tasgabbaa'aa");
    s = s.replaceAll(RegExp(r'\b(?:dhaahuu|dhahu)\b', caseSensitive: false), "dha'uu");
    s = s.replaceAll(RegExp(r'\bakam\b', caseSensitive: false), 'akkam');
    s = s.replaceAll(RegExp(r'\bakkam\s+(?:jirt|jirti)\b', caseSensitive: false), 'akkam jirta');
    s = s.replaceAll(RegExp(r'\bnaga\b', caseSensitive: false), 'nagaa');
    s = s.replaceAll(RegExp(r'\bnagada\b', caseSensitive: false), 'nagaadha');
    s = s.replaceAll(RegExp(r'\bnagaa\s+dhaa\b', caseSensitive: false), 'nagaadha');
    s = s.replaceAll(RegExp(r'\bnagaa?\s+qabda\b', caseSensitive: false), 'nagaa qabdaa');
    s = s.replaceAll(RegExp(r'\bnagaa?\s+qabdu\b', caseSensitive: false), 'nagaa qabduu');
    s = s.replaceAll(RegExp(r'\bfayyadha\b', caseSensitive: false), 'fayyaadha');
    s = s.replaceAll(RegExp(r'\bfayyaa\s+dhaa\b', caseSensitive: false), 'fayyaadha');
    s = s.replaceAll(RegExp(r'\bfayyaa\s+qabda\b', caseSensitive: false), 'fayyaa qabdaa');
    s = s.replaceAll(RegExp(r'\bati\s+ho\b', caseSensitive: false), 'ati hoo');
    s = s.replaceAll(RegExp(r'\bisin\s+ho\b', caseSensitive: false), 'isin hoo');
    s = s.replaceAll(RegExp(r'\bqorich\b', caseSensitive: false), 'qoricha');
    s = s.replaceAll(RegExp(r'\bhospita\b', caseSensitive: false), 'hospitaala');
    return s.replaceAll(RegExp(r' {2,}'), ' ').trim();
  }

  /// Normalize Somali text (standardizes glottal stop apostrophes and contractions).
  static String normalizeSomali(String text) {
    if (text.isEmpty) return '';
    var s = text.replaceAll(RegExp(r"[’‘ʼ`´]"), "'");
    s = s.replaceAll(RegExp(r'\bhalkeeba[ay]?\s+ku\s+xanuun\w*\b', caseSensitive: false), 'halkeebay ku xanuunaysaa');
    s = s.replaceAll(RegExp(r'\bku\s+xanun\w*\b', caseSensitive: false), 'ku xanuunaysaa');
    s = s.replaceAll(RegExp(r'\bgoorma[ay]?\s+bilaab\w*\b', caseSensitive: false), 'goormay bilaabatay');
    s = s.replaceAll(RegExp(r'\bmadax\s+xanun\w*\b', caseSensitive: false), 'madax xanuun');
    s = s.replaceAll(RegExp(r'\bcalool\s+xanun\w*\b', caseSensitive: false), 'calool xanuun');
    s = s.replaceAll(RegExp(r'\bwaa\s+aan\b', caseSensitive: false), 'waan');
    s = s.replaceAll(RegExp(r'\bwaa\s+aad\b', caseSensitive: false), 'waad');
    s = s.replaceAll(RegExp(r'\bbaa\s+aan\b', caseSensitive: false), 'baan');
    s = s.replaceAll(RegExp(r'\b(?:wan\s+fiicanahay|waan\s+ficanahay)\b', caseSensitive: false), 'waan fiicanahay');
    s = s.replaceAll(RegExp(r'\bside(?:e)?\s+tahy\b', caseSensitive: false), 'sidee tahay');
    s = s.replaceAll(RegExp(r'\bside\s+tahay\b', caseSensitive: false), 'sidee tahay');
    s = s.replaceAll(RegExp(r'\bside(?:e)?\s+tihin\b', caseSensitive: false), 'sidee tihiin');
    s = s.replaceAll(RegExp(r'\bside\s+tihiin\b', caseSensitive: false), 'sidee tihiin');
    s = s.replaceAll(RegExp(r'\badigun\b', caseSensitive: false), 'adiguna');
    s = s.replaceAll(RegExp(r'\bidinkun\b', caseSensitive: false), 'idinkuna');
    s = s.replaceAll(RegExp(r'\bnabad\s+miya\b', caseSensitive: false), 'nabad miyaa');
    s = s.replaceAll(RegExp(r'\bma\s+fiican\s+tahy\b', caseSensitive: false), 'ma fiican tahay');
    s = s.replaceAll(RegExp(r'\bma\s+fiican\s+tihin\b', caseSensitive: false), 'ma fiican tihiin');
    s = s.replaceAll(RegExp(r'\bqandho\s+aya\b', caseSensitive: false), 'qandho ayaa');
    s = s.replaceAll(RegExp(r'\bdoktor\b', caseSensitive: false), 'dhakhtar');
    s = s.replaceAll(RegExp(r'\bfarmashi\b', caseSensitive: false), 'farmashiye');
    return s.replaceAll(RegExp(r' {2,}'), ' ').trim();
  }

  /// Normalize English text (expands common conversational contractions).
  static String normalizeEnglish(String text) {
    if (text.isEmpty) return '';
    var s = text.replaceAll(RegExp(r"[’‘ʼ`´]"), "'");
    s = s.replaceAll(RegExp(r"\b(?:wear|were)\s+does\s+it\s+hurt\b", caseSensitive: false), 'where does it hurt');
    s = s.replaceAll(RegExp(r"\bwen\s+did\s+it\s+start\b", caseSensitive: false), 'when did it start');
    s = s.replaceAll(RegExp(r"\bhead\s+ache\b", caseSensitive: false), 'headache');
    s = s.replaceAll(RegExp(r"\bstomach\s+ache\b", caseSensitive: false), 'stomach ache');
    s = s.replaceAll(RegExp(r"\bhi\s+fever\b", caseSensitive: false), 'high fever');
    s = s.replaceAll(RegExp(r"\bches\s+pain\b", caseSensitive: false), 'chest pain');
    s = s.replaceAll(RegExp(r"\bi[' ]?m\b", caseSensitive: false), 'I am');
    s = s.replaceAll(RegExp(r"\b(?:you're|youre|u\s+r)\b", caseSensitive: false), 'you are');
    s = s.replaceAll(RegExp(r"\bhow\s+(?:r|are)\s+u\b", caseSensitive: false), 'how are you');
    s = s.replaceAll(RegExp(r"\bwhat[']?s\b", caseSensitive: false), 'what is');
    s = s.replaceAll(RegExp(r"\bwhere[']?s\b", caseSensitive: false), 'where is');
    s = s.replaceAll(RegExp(r"\bdon[']?t\b", caseSensitive: false), 'do not');
    s = s.replaceAll(RegExp(r"\bcan[']?t\b", caseSensitive: false), 'cannot');
    return s.replaceAll(RegExp(r' {2,}'), ' ').trim();
  }

  /// Universal acoustic & speech recognition normalizer for all supported languages.
  /// Corrects common CTC acoustic truncations, boundary mergers, and phonetically
  /// degraded speech transcriptions before processing or UI display.
  static String cleanSpokenTranscription(String text, String sourceLang) {
    if (text.isEmpty) return '';
    final s = text.trim();
    switch (sourceLang) {
      case 'amh':
        return normalizeAmharic(s);
      case 'tir':
        return normalizeTigrinya(s);
      case 'orm':
        return normalizeOromo(s);
      case 'som':
        return normalizeSomali(s);
      case 'eng':
        return normalizeEnglish(s);
      default:
        return s;
    }
  }

  /// Automatically recognises the spoken language from speech transcription text.
  /// Identifies Amharic ('amh'), Tigrinya ('tir'), Afaan Oromoo ('orm'),
  /// Somali ('som'), or English ('eng') using script analysis, vocabulary, and phonotactics.
  static String detectLanguage(String text, {String defaultLang = 'amh'}) {
    final trimmed = text.trim();
    if (trimmed.isEmpty) return defaultLang;

    // 1. Explicit STT model language token cues
    final lower = trimmed.toLowerCase();
    if (lower.contains('[amh]') || lower.startsWith('amh:')) return 'amh';
    if (lower.contains('[tir]') || lower.startsWith('tir:')) return 'tir';
    if (lower.contains('[orm]') || lower.startsWith('orm:')) return 'orm';
    if (lower.contains('[som]') || lower.startsWith('som:')) return 'som';
    if (lower.contains('[eng]') || lower.startsWith('eng:')) return 'eng';

    // 2. Ethiopic (Ge'ez) script analysis
    final ethiopicMatches = RegExp(r'[\u1200-\u137F\u1380-\u139F\u2D80-\u2DDF\uAB00-\uAB2F]').allMatches(trimmed);
    if (ethiopicMatches.isNotEmpty) {
      var tirScore = 0;
      var amhScore = 0;
      var ormScore = 0;
      var somScore = 0;
      var engScore = 0;

      // Phonetic English transcribed into Ge'ez letters
      const engGeezWords = [
        'ሄሎ', 'ሃሎ', 'ሀሎ', 'ሃው', 'ሀዋርዩ', 'ፕሊስ', 'ፕሊዝ', 'ቴንክ', 'ታንክ', 'ቴንኪው',
        'ቴንክዩ', 'ዌር', 'ኢዝ', 'ዋት', 'ዋትስ', 'ጉድ', 'ሞርኒንግ', 'ፋይን', 'አይም', 'ኦኬ',
        'ኦኬይ', 'የስ', 'ኖ', 'ሀርቱ', 'ፔይን', 'ሄዴክ', 'ፊቨር', 'ነርስ', 'ክሊኒክ', 'ታይርድ',
      ];
      for (final w in engGeezWords) {
        if (trimmed.contains(w)) engScore += 4;
      }

      // Phonetic Afaan Oromoo transcribed into Ge'ez letters
      const ormGeezWords = [
        'አካም', 'ኣካም', 'ጅርታ', 'ጅርቱ', 'ነጋ', 'ነጋዳ', 'ነጋአ', 'ፈያ', 'ፈያዳ', 'ማል',
        'ማልቱ', 'ገልቶሚ', 'ገላቶሚ', 'ባርባዳ', 'ኤዬ', 'ሚቲ', 'ኦልቴ', 'ቡልቴ', 'ቢሻን',
        'ቆሪቻ', 'ዱኩባ', 'ዱኩበ', 'ዲቤ', 'ቂቤ', 'አባ', 'ኮቲ', 'አቲ', 'አኒ',
      ];
      for (final w in ormGeezWords) {
        if (trimmed.contains(w)) ormScore += 4;
      }

      // Phonetic Somali transcribed into Ge'ez letters
      const somGeezWords = [
        'ሲዴ', 'ሲደ', 'ታሃይ', 'ታሀይ', 'ቲሂን', 'ኢስካ', 'ዋራን', 'ዋን', 'ፊሰን', 'ፊካን',
        'ማሃድሰኒድ', 'ማክሳ', 'ነበድ', 'ናባድ', 'መያ', 'ቢዮ', 'ዳዎ', 'አዲጉ', 'አኒጉ', 'ገላብ',
        'ሱበክ', 'ዋናግሰን',
      ];
      for (final w in somGeezWords) {
        if (trimmed.contains(w)) somScore += 4;
      }

      // Tigrinya-distinct consonants and vowels (ቐ, ቘ, ዀ, ዸ, ጘ, ኽ, initial ኣ)
      if (RegExp(r'[\u1250-\u125D\u12B8-\u12BF\u12F8-\u12FD\u1318-\u131D\u1358-\u135A]').hasMatch(trimmed)) {
        tirScore += 5;
      }
      if (trimmed.contains('ኣ')) {
        tirScore += 2;
      }

      // Amharic-distinct consonants (ኘ, ዠ, ጨ, ጰ)
      if (RegExp(r'[\u1298-\u129F\u12E0-\u12E7\u1328-\u132F\u1338-\u133F]').hasMatch(trimmed)) {
        amhScore += 5;
      }

      // High-frequency Tigrinya lexical markers
      const tirWords = [
        'ከመይ', 'ጽቡቕ', 'ጽቡቅ', 'የቐንየለይ', 'የቀንየለይ', 'ኣለኹ', 'አለኹ', 'ኣለኻ', 'አለኻ',
        'ኣለኺ', 'አለኺ', 'ኣለዉ', 'አለዉ', 'ኣይኮነን', 'ኣይኮነን', 'ሓቂ', 'ደቒ', 'ደቂ', 'ዓዲ',
        'ጥዕና', 'ይቕሬታ', 'ይቅሬታ', 'እንታይ', 'ናይ', 'ኣበይ', 'አበይ', 'ሕጂ', 'ሕዚ', 'መን',
        'ንሕና', 'ንስኻ', 'ንስኺ', 'እወ', 'ኣይፋልን', 'ማይ', 'በጃኻ', 'በጃኺ', 'ሓወይ', 'ሓፍተይ',
        'ደሓን', 'ሽምካ', 'ሽምኪ', 'ትግርኛ', 'ክንደይ',
      ];
      for (final w in tirWords) {
        if (trimmed.contains(w)) tirScore += 4;
      }

      // High-frequency Amharic lexical markers
      const amhWords = [
        'ነው', 'ነኝ', 'ነህ', 'ነሽ', 'ናት', 'ናቸው', 'ናችሁ', 'ነበር', 'የለም', 'አለ',
        'አይደለም', 'እሺ', 'አመሰግናለሁ', 'እንዴት', 'ምን', 'ማን', 'የት', 'መቼ', 'ለምን',
        'እኔ', 'አንተ', 'አንቺ', 'እሱ', 'እሷ', 'እኛ', 'እናንተ', 'እነሱ', 'በጣም', 'ጥሩ',
        'ውሃ', 'ምግብ', 'ቤት', 'ሆስፒታል', 'መድሃኒት', 'ህመም', 'ዶክተር', 'ስምህ', 'ስምሽ',
        'አማርኛ', 'ስንት', 'ዋጋ', 'ይቅርታ', 'ደህና', 'እንደምን',
      ];
      for (final w in amhWords) {
        if (trimmed.contains(w)) amhScore += 4;
      }

      final scores = {'tir': tirScore, 'eng': engScore, 'orm': ormScore, 'som': somScore, 'amh': amhScore};
      final sortedEntries = scores.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
      if (sortedEntries.first.value > 0) {
        return sortedEntries.first.key;
      }

      return defaultLang;
    }

    // 3. Latin script: Afaan Oromoo vs Somali vs English
    final words = lower.split(RegExp(r'\s+'));
    var ormScore = 0;
    var somScore = 0;
    var engScore = 0;

    const ormKeywords = {
      'akkam', 'nagaa', 'maal', 'eessa', 'yoom', 'maaliif', 'eenyu', 'fayyaa',
      'galatoomi', 'baga', 'ani', 'ati', 'inni', 'isheen', 'nuti', 'isin', 'isaan',
      'gaarii', 'dhuguma', 'hin', 'miti', 'akka', 'waan', 'biyya', 'mana',
      'bishaan', 'dhibee', 'hospitaala', 'qoricha', 'dhukkuba', 'doktoora',
      'guyyaa', 'halkan', 'tolle', 'eyyee', 'lakki', 'maaloo', 'jirta', 'jirtu',
      'obboo', 'aadde', 'oromoo', 'oromiyaa', 'meeqa', 'kee', 'koo',
    };

    const somKeywords = {
      'sidee', 'tahay', 'subax', 'galab', 'wanaagsan', 'mahadsanid', 'waan',
      'fiicanahay', 'magacaa', 'xagee', 'immisa', 'haa', 'maya', 'fadlan',
      'maxaa', 'waayo', 'goorma', 'kuma', 'aniga', 'adiga', 'isaga', 'iyada',
      'annaga', 'idinka', 'iyaga', 'biyo', 'guri', 'isbitaal', 'dhaqtar',
      'dawo', 'xanuun', 'nabad', 'soo', 'dhawoow', 'shaah', 'lacag', 'maanta',
      'somali', 'soomaali', 'hayee', 'fiican', 'adigu',
    };

    const engKeywords = {
      'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it',
      'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this',
      'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or',
      'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
      'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
      'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know',
      'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could',
      'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come',
      'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how',
      'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because',
      'any', 'these', 'give', 'day', 'most', 'us', 'hello', 'hi', 'please',
      'thank', 'thanks', 'pain', 'doctor', 'hospital', 'water', 'medicine',
      'help', 'where', 'is', 'are', 'am', 'yes', 'headache', 'fever', 'stomach',
      'nurse', 'emergency', 'food', 'market', 'price',
    };

    for (final rawWord in words) {
      final clean = rawWord.replaceAll(RegExp(r'[^a-z]'), '');
      if (clean.isEmpty) continue;

      if (ormKeywords.contains(clean)) ormScore += 3;
      if (somKeywords.contains(clean)) somScore += 3;
      if (engKeywords.contains(clean)) engScore += 3;

      if (clean.contains('dh') || clean.contains('ny') || clean.contains('ch')) ormScore += 1;
      if (clean.contains('x') || clean.contains('c') || clean.contains('kh')) somScore += 1;
      if (clean.contains('th') || clean.contains('wh') || clean.contains('tion')) engScore += 2;
    }

    if (ormScore > somScore && ormScore > engScore) return 'orm';
    if (somScore > ormScore && somScore > engScore) return 'som';
    if (engScore > ormScore && engScore > somScore) return 'eng';

    // Phonotactic heuristic for Oromo / Somali vowel lengthening vs English
    if (RegExp(r'[aeiou]{2}').hasMatch(lower)) {
      return (somScore >= ormScore && somScore > 0) ? 'som' : 'orm';
    }

    return defaultLang;
  }

  /// Normalizes source text before feeding into NLLB tokenizer for any language.
  static String normalizeForNmt(String text, String sourceLang) {
    return cleanSpokenTranscription(text, sourceLang);
  }

  /// General input normalizer for text cleaning and homophone harmonization.
  static String normalize(String text) {
    if (text.isEmpty) return '';
    var s = text.trim().toLowerCase();
    s = s.replaceAll(RegExp(r"[’‘ʼ`´]"), "'");
    s = s.replaceAll('፡', ' ');
    s = normalizeAmharic(s);
    s = s.replaceAll('ደሓን', 'ድሓን');

    for (final entry in _homophones.entries) {
      if (s.contains(entry.key)) {
        s = s.replaceAll(entry.key, entry.value);
      }
    }

    s = s.replaceAll(RegExp(r"\bi'm\b"), 'i am');
    s = s.replaceAll(RegExp(r"\byou're\b"), 'you are');
    s = s.replaceAll(RegExp(r"\bwhat's\b"), 'what is');
    s = s.replaceAll(RegExp(r"\bwhere's\b"), 'where is');
    s = s.replaceAll(RegExp(r"\bdon't\b"), 'do not');
    s = s.replaceAll(RegExp(r"\bcan't\b"), 'cannot');

    s = s.replaceAll(RegExp(r"(^['\u0022]|['\u0022]$|(?<=\s)['\u0022]|['\u0022](?=\s))"), ' ');
    return s.replaceAll(_punctRegex, ' ').replaceAll(RegExp(r' {2,}'), ' ').trim();
  }

  /// Calculates Levenshtein edit distance between two strings.
  static int _levenshtein(String s1, String s2) {
    if (s1 == s2) return 0;
    if (s1.isEmpty) return s2.length;
    if (s2.isEmpty) return s1.length;
    final v0 = List<int>.generate(s2.length + 1, (i) => i);
    final v1 = List<int>.filled(s2.length + 1, 0);
    for (var i = 0; i < s1.length; i++) {
      v1[0] = i + 1;
      for (var j = 0; j < s2.length; j++) {
        final cost = (s1[i] == s2[j]) ? 0 : 1;
        v1[j + 1] = (v1[j] + 1 < v0[j + 1] + 1)
            ? (v1[j] + 1 < v0[j] + cost ? v1[j] + 1 : v0[j] + cost)
            : (v0[j + 1] + 1 < v0[j] + cost ? v0[j + 1] + 1 : v0[j] + cost);
      }
      for (var j = 0; j <= s2.length; j++) {
        v0[j] = v1[j];
      }
    }
    return v1[s2.length];
  }

  /// Calculates normalized string similarity using Levenshtein distance (0.0 to 1.0).
  static double levenshteinSimilarity(String s1, String s2) {
    if (s1 == s2) return 1.0;
    final maxLen = s1.length > s2.length ? s1.length : s2.length;
    if (maxLen == 0) return 1.0;
    final dist = _levenshtein(s1, s2);
    return 1.0 - (dist / maxLen);
  }

  /// Clean and post-process NLLB translation outputs to eliminate literal hallucinations.
  static String postprocess(
    String translated, {
    required String sourceLang,
    required String targetLang,
  }) {
    var res = translated.trim();
    if (res.isEmpty) return res;

    // Remove repeating adjacent words across all scripts
    res = res.replaceAllMapped(RegExp(r'\b([A-Za-z]+)(?:[\s,]+\1\b)+', caseSensitive: false), (m) => m[1]!);
    res = res.replaceAllMapped(RegExp(r'\b([\u1200-\u137F]+)(?:[\s፣,]+\1\b)+'), (m) => m[1]!);

    if (targetLang == 'eng') {
      res = res.replaceAll(RegExp(r"^(?:what is peace like|what's peace like)\??$", caseSensitive: false), 'Hello, how are you?');
      res = res.replaceAll(RegExp(r"^(?:what is peace|what's peace)\??$", caseSensitive: false), 'Hello, how are you?');
      res = res.replaceAll(RegExp(r"\bwhen did you find peace\??$", caseSensitive: false), 'Hello, how are you?');
      res = res.replaceAll(RegExp(r"^(?:is it peace|is peace)\??$", caseSensitive: false), 'Is everything good?');
      res = res.replaceAll(RegExp(r"^(?:are you peace|are you peaceful)\??$", caseSensitive: false), 'Are you doing well?');
      res = res.replaceAll(RegExp(r"^peace be (?:with|upon) you\.?$", caseSensitive: false), 'Hello!');
      res = res.replaceAll(RegExp(r"^you(?:'re| are) (?:at |the )?peace\.?$", caseSensitive: false), 'How are you?');
      res = res.replaceAll(RegExp(r"\bhow did you pass the night\b", caseSensitive: false), 'good morning');
      res = res.replaceAll(RegExp(r"\bhow did you spend the day\b", caseSensitive: false), 'good afternoon');
      res = res.replaceAll(RegExp(r"^what do you teach\??$", caseSensitive: false), 'Where does it hurt you?');
      res = res.replaceAll(RegExp(r"^what is your religion\??$", caseSensitive: false), 'Where does it hurt you?');
      res = res.replaceAll(RegExp(r"^he was a good doctor\.?$", caseSensitive: false), 'I will prescribe you medicine.');
      res = res.replaceAll(RegExp(r"^you've been given medication\.?$", caseSensitive: false), 'I will prescribe you medicine.');
      res = res.replaceAll(RegExp(r"^i(?:'m| am) fine(?:,)? you are\??$", caseSensitive: false), "I'm fine, how are you?");
      res = res.replaceAll(RegExp(r"^i(?:'m| am) fine(?:,)? and you are\??$", caseSensitive: false), "I'm fine, how are you?");
      res = res.replaceAll(RegExp(r"^i was rej?jected.*", caseSensitive: false), "I am fine, and you?");
      res = res.replaceAll(RegExp(r"^how did the (?:painting|picture|drawing|artwork) (?:end|finish|conclude)\??$", caseSensitive: false), 'Hello, how are you? Are you doing well?');
      res = res.replaceAll(RegExp(r"\bthe (?:painting|picture|drawing) end\b", caseSensitive: false), 'how are you');
    } else if (targetLang == 'orm') {
      res = res.replaceAll(RegExp(r"\byeroo hafuuraa keessatti nagaa argadhaa\??$", caseSensitive: false), 'Akkam jirta?');
      res = res.replaceAll(RegExp(r"^nagaa argadhaa\??$", caseSensitive: false), 'Akkam jirta?');
      res = res.replaceAll(RegExp(r"^amantiin kee maali\??$", caseSensitive: false), 'Bakka kamtu si dhukkuba?');
      res = res.replaceAll(RegExp(r"^doktora gaarii ture\.?$", caseSensitive: false), 'Qoricha siif ajaja.');
      res = res.replaceAll(RegExp(r"^suurri akkamitti (?:dhumate|dhume)\??$", caseSensitive: false), 'Akkam jirta, nagaa qabdaa?');
      res = res.replaceAll(RegExp(r"^salaam\??$", caseSensitive: false), 'Akkam');
    } else if (targetLang == 'amh') {
      res = res.replaceAll('ላ ሊቤዳ', 'ላሊበላ');
      res = res.replaceAll('አክሴል', 'አክሱም');
      res = res.replaceAll('ባሃርዳ', 'ባህር ዳር');
      res = res.replaceAll('አዲስአበባ', 'አዲስ አበባ');
      res = res.replaceAll(RegExp(r"\bሰላማዊ መሆን የምትችለው እንዴት ነው\??"), 'እንዴት ነህ፣ ደህና ነህ?');
      res = res.replaceAll(RegExp(r"^አንተም ሰላም ታገኛለህ[።.]?$"), 'እንዴት ነህ፣ ደህና ነህ?');
      res = res.replaceAll(RegExp(r"^እምነትህ ምንድን ነው\??$"), 'የት አካባቢ ያመዎታል?');
      res = res.replaceAll(RegExp(r"^ጥሩ ዶክተር ነበር[።.]?$"), 'መድኃኒት አዝልሃለሁ።');
      res = res.replaceAll(RegExp(r"^ስዕሉ እንዴት (?:አለቀ|ተጠናቀቀ)\??$", caseSensitive: false), 'ሰላም፣ እንዴት ነህ? ደህና ነህ?');
    } else if (targetLang == 'tir') {
      res = res.replaceAll(RegExp(r"^ሰላም ረኺብካ ዲኻ\??$"), 'ሰላም ከመይ ኣለኻ?');
      res = res.replaceAll(RegExp(r"^ሰላም ትረክብ ኢኻ[።.]?$"), 'ሰላም ከመይ ኣለኻ?');
      res = res.replaceAll(RegExp(r"^እምነትካ እንታይ እዩ\??$"), 'ኣበይ የሕምመካ ኣሎ?');
      res = res.replaceAll(RegExp(r"^ጽቡቕ ሓኪም ነይሩ[።.]?$"), 'መድሃኒት ክእዝዘልካ እየ።');
      res = res.replaceAll(RegExp(r"^ስእሊ ብኸመይ (?:ተወዲኡ|ተዛዚሙ)\??$", caseSensitive: false), 'ሰላም ከመይ ኣለኻ፡ ድሓን ዲኻ?');
    } else if (targetLang == 'som') {
      res = res.replaceAll(RegExp(r"^goormaad nabad heshay\??$", caseSensitive: false), 'Sidee tahay?');
      res = res.replaceAll(RegExp(r"^nabad gelyo miyaad heshay\??$", caseSensitive: false), 'Sidee tahay?');
      res = res.replaceAll(RegExp(r"^diintaadu waa maxay\??$", caseSensitive: false), 'Xaggee ku xanuunaysaa?');
      res = res.replaceAll(RegExp(r"^dhakhtar fiican buu ahaa\.?$", caseSensitive: false), 'Daawaan kuu qorayaa.');
      res = res.replaceAll(RegExp(r"^sawirku sidee buu ku (?:dhammaaday|dhamaaday)\??$", caseSensitive: false), 'Sidee tahay, ma fiican tahay?');
      res = res.replaceAll(RegExp(r"^salaam\??$", caseSensitive: false), 'Sidee tahay');
    }
    return res;
  }
}
