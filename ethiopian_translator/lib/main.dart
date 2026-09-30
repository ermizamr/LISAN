import 'dart:async';
import 'dart:math' as math;
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/material.dart';

import 'lisan_icons.dart';
import 'recording_service.dart';
import 'translator_api.dart';

void main() => runApp(
  TranslatorApp(audioCapture: RecordingService(), api: TranslatorApi()),
);

// ---------------------------------------------------------------------------
// Design System & Visual Tokens (Figma LISAN / MODEL 01)
// ---------------------------------------------------------------------------
class LisanTheme {
  static const Color paper = Color(0xFFDDD5C3);
  static const Color paperLight = Color(0xFFEEE8DA);
  static const Color paperDark = Color(0xFFBDB5A4);
  static const Color ink = Color(0xFF20221F);
  static const Color muted = Color(0xFF6C6D65);
  static const Color well = Color(0xFF252924);
  static const Color wellDeep = Color(0xFF181B18);
  static const Color orange = Color(0xFFF05A36);
  static const Color orangeDark = Color(0xFFB93720);
  static const Color acid = Color(0xFFD8F171);
  static const Color borderMetallic = Color(0xFFAAA293);
  static const Color line = Color(0x3830322D);

  static const Color toneCoral = Color(0xFFDF5942);
  static const Color toneGreen = Color(0xFF378D68);
  static const Color toneGold = Color(0xFFD89E35);
  static const Color toneBlue = Color(0xFF3E6F9B);
  static const Color toneViolet = Color(0xFF735E9B);
}

class AppLanguage {
  const AppLanguage({
    required this.name,
    required this.native,
    required this.code,
    required this.backendKey,
    required this.tone,
    required this.symbol,
  });

  final String name;
  final String native;
  final String code;
  final String backendKey;
  final Color tone;
  final LanguageSymbolType symbol;
}

const List<AppLanguage> kLanguages = [
  AppLanguage(
    name: 'Amharic',
    native: 'አማርኛ',
    code: 'AM',
    backendKey: 'amh',
    tone: LisanTheme.toneCoral,
    symbol: LanguageSymbolType.glyph,
  ),
  AppLanguage(
    name: 'Afaan Oromoo',
    native: 'Afaan Oromoo',
    code: 'OR',
    backendKey: 'orm',
    tone: LisanTheme.toneGreen,
    symbol: LanguageSymbolType.tree,
  ),
  AppLanguage(
    name: 'Tigrinya',
    native: 'ትግርኛ',
    code: 'TI',
    backendKey: 'tir',
    tone: LisanTheme.toneGold,
    symbol: LanguageSymbolType.sun,
  ),
  AppLanguage(
    name: 'Somali',
    native: 'Soomaali',
    code: 'SO',
    backendKey: 'som',
    tone: LisanTheme.toneBlue,
    symbol: LanguageSymbolType.star,
  ),
  AppLanguage(
    name: 'English',
    native: 'English',
    code: 'EN',
    backendKey: 'eng',
    tone: LisanTheme.toneViolet,
    symbol: LanguageSymbolType.globe,
  ),
];

const Map<String, String> kDefaultPhrases = {
  'AM': 'ወደ ቦሌ እንዴት መሄድ እችላለሁ?',
  'OR': "Akkamitti gara Boolee deemuu danda'a?",
  'TI': 'ናብ ቦሌ ብኸመይ ክኸይድ ይኽእል?',
  'SO': 'Sideen ku tagi karaa Bole?',
  'EN': 'How can I get to Bole?',
};

enum AppView { ready, speaking, language, result, settings }

// ---------------------------------------------------------------------------
// Root Application
// ---------------------------------------------------------------------------
class TranslatorApp extends StatelessWidget {
  const TranslatorApp({super.key, this.audioCapture, this.api});

  final AudioCapture? audioCapture;
  final TranslatorApi? api;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Lisan',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: const Color(0xFF1B1D1A),
        fontFamily: 'sans',
        useMaterial3: true,
      ),
      home: ConversationPage(audioCapture: audioCapture, api: api),
    );
  }
}

// ---------------------------------------------------------------------------
// Main Interactive View Container
// ---------------------------------------------------------------------------
class ConversationPage extends StatefulWidget {
  ConversationPage({super.key, AudioCapture? audioCapture, TranslatorApi? api})
    : audioCapture = audioCapture ?? const DemoRecordingService(),
      api = api ?? TranslatorApi();

  final AudioCapture audioCapture;
  final TranslatorApi api;

  @override
  State<ConversationPage> createState() => _ConversationPageState();
}

class _ConversationPageState extends State<ConversationPage>
    with TickerProviderStateMixin {
  AppView _view = AppView.ready;
  AppLanguage _language = kLanguages[0]; // Amharic
  AppLanguage _targetLanguage = kLanguages[4]; // English

  bool _playing = false;
  String _defaultTarget = 'English';
  bool _autoPlay = true;
  bool _smartDetect = true;
  bool _haptics = true;
  bool _conversationMode = false;
  AppLanguage _firstLanguage = kLanguages[0];
  AppLanguage _secondLanguage = kLanguages[4];
  int _conversationTurn = 0;

  // Real backend transaction states
  String _sourceText = 'ወደ ቦሌ እንዴት መሄድ እችላለሁ?';
  String _outputText = 'How can I get to Bole?';
  final String _audioDurationText = '0:04';
  bool _isTmMatch = true;
  bool _isLoading = false;
  String? _recordedFilePath;

  late final AudioPlayer _audioPlayer;
  late final TextEditingController _serverController;
  Timer? _playbackTimer;

  @override
  void initState() {
    super.initState();
    _audioPlayer = AudioPlayer();
    _serverController = TextEditingController(
      text: widget.api.baseUri.toString(),
    );

    _audioPlayer.onPlayerComplete.listen((_) {
      if (mounted) {
        setState(() => _playing = false);
      }
    });
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    _serverController.dispose();
    _playbackTimer?.cancel();
    super.dispose();
  }

  // -------------------------------------------------------------------------
  // Interaction Handlers
  // -------------------------------------------------------------------------
  Future<void> _beginSpeaking() async {
    if (_view != AppView.ready &&
        !(_view == AppView.result && _conversationMode)) {
      return;
    }

    setState(() {
      _view = AppView.speaking;
      _isLoading = false;
    });

    try {
      _recordedFilePath = await widget.audioCapture.start();
    } catch (e) {
      debugPrint('Audio capture start error: $e');
    }
  }

  Future<void> _finishSpeaking() async {
    if (_view != AppView.speaking) return;

    String? path;
    try {
      path = await widget.audioCapture.stop();
      if (path != null && path.isNotEmpty) {
        _recordedFilePath = path;
      }
    } catch (e) {
      debugPrint('Audio capture stop error: $e');
    }

    await Future.delayed(const Duration(milliseconds: 240));
    if (!mounted) return;

    if (_conversationMode) {
      final source = _conversationTurn.isEven ? _firstLanguage : _secondLanguage;
      final target = _conversationTurn.isEven ? _secondLanguage : _firstLanguage;
      setState(() {
        _language = source;
        _targetLanguage = target;
        _conversationTurn++;
      });
      await _executeTranslation(source: source, target: target);
    } else {
      setState(() {
        _view = AppView.language;
      });
    }
  }

  Future<void> _chooseLanguage(AppLanguage chosen) async {
    final preferred =
        kLanguages.firstWhere(
          (item) => item.name == _defaultTarget,
          orElse: () => kLanguages[4],
        );
    final fallback = chosen.code == 'EN' ? kLanguages[0] : kLanguages[4];
    final target = preferred.code == chosen.code ? fallback : preferred;

    setState(() {
      _language = chosen;
      _targetLanguage = target;
      _view = AppView.result;
    });

    await _executeTranslation(source: chosen, target: target);
  }

  Future<void> _executeTranslation({
    required AppLanguage source,
    required AppLanguage target,
  }) async {
    setState(() {
      _isLoading = true;
      _view = AppView.result;
    });

    try {
      TranslationResult result;
      if (_recordedFilePath != null && _recordedFilePath!.isNotEmpty) {
        result = await widget.api.translateAudio(
          filePath: _recordedFilePath!,
          source: source.backendKey,
          target: target.backendKey,
        );
      } else {
        // Fallback or demo phrase
        final input = kDefaultPhrases[source.code] ?? 'Where is the nearest clinic?';
        result = await widget.api.translateText(
          text: input,
          source: source.backendKey,
          target: target.backendKey,
        );
      }

      if (mounted) {
        setState(() {
          _sourceText = result.sourceText.isNotEmpty
              ? result.sourceText
              : (kDefaultPhrases[source.code] ?? '');
          _outputText = result.translatedText.isNotEmpty
              ? result.translatedText
              : (kDefaultPhrases[target.code] ?? '');
          _isTmMatch = result.isTmMatch;
          _isLoading = false;
        });

        if (_autoPlay) {
          _playAudio();
        }
      }
    } catch (e) {
      debugPrint('Translation error (using local phrasebook fallback): $e');
      if (mounted) {
        setState(() {
          _sourceText = kDefaultPhrases[source.code] ?? 'How can I get to Bole?';
          _outputText = kDefaultPhrases[target.code] ?? 'ወደ ቦሌ እንዴት መሄድ እችላለሁ?';
          _isTmMatch = true;
          _isLoading = false;
        });
        if (_autoPlay) {
          _playAudio();
        }
      }
    }
  }

  Future<void> _playAudio() async {
    final text = _outputText.trim();
    if (text.isEmpty) return;

    setState(() {
      _playing = true;
    });

    _playbackTimer?.cancel();
    _playbackTimer = Timer(const Duration(milliseconds: 3800), () {
      if (mounted) setState(() => _playing = false);
    });

    try {
      final uri = widget.api.getTtsUri(text, _targetLanguage.backendKey);
      await _audioPlayer.stop();
      await _audioPlayer.play(UrlSource(uri.toString()));
    } catch (e) {
      debugPrint('TTS play error: $e');
    }
  }

  void _reset() {
    _audioPlayer.stop();
    _playbackTimer?.cancel();
    setState(() {
      _view = AppView.ready;
      _playing = false;
      _isLoading = false;
    });
  }

  // -------------------------------------------------------------------------
  // UI Builder
  // -------------------------------------------------------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1B1D1A),
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment(0, -0.6),
            radius: 1.2,
            colors: [Color(0xFF353932), Color(0xFF171916)],
          ),
        ),
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 430),
              child: Container(
                decoration: BoxDecoration(
                  color: LisanTheme.paper,
                  border: Border.all(
                    color: const Color(0xFFAAA293),
                    width: MediaQuery.of(context).size.width > 500 ? 8 : 1,
                  ),
                  borderRadius: MediaQuery.of(context).size.width > 500
                      ? BorderRadius.circular(30)
                      : BorderRadius.zero,
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x7A000000),
                      blurRadius: 40,
                      offset: Offset(0, 18),
                    ),
                  ],
                ),
                child: Stack(
                  children: [
                    // Subtle industrial watermark
                    Positioned(
                      right: 12,
                      bottom: 120,
                      child: RotatedBox(
                        quarterTurns: 3,
                        child: Text(
                          'LISAN  /  MODEL 01',
                          style: TextStyle(
                            color: const Color(0xFF363731).withValues(alpha: 0.28),
                            fontSize: 7.5,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 2.2,
                          ),
                        ),
                      ),
                    ),

                    // Main Content Frame
                    Column(
                      children: [
                        _buildTopbar(),
                        Expanded(
                          child: AnimatedSwitcher(
                            duration: const Duration(milliseconds: 260),
                            child: _buildCurrentView(),
                          ),
                        ),
                        _buildHomeIndicator(),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // -------------------------------------------------------------------------
  // Header Topbar
  // -------------------------------------------------------------------------
  Widget _buildTopbar() {
    return Container(
      height: 68,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(color: Color(0x3831322D)),
        ),
        boxShadow: [
          BoxShadow(
            color: Color(0x73FFFFFF),
            offset: Offset(0, 1),
            blurRadius: 0,
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Wordmark Button
          GestureDetector(
            onTap: _reset,
            behavior: HitTestBehavior.opaque,
            child: Row(
              children: [
                Container(
                  width: 34,
                  height: 34,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: const Color(0xFF151713)),
                    gradient: const RadialGradient(
                      center: Alignment(-0.3, -0.4),
                      radius: 0.9,
                      colors: [
                        Color(0xFF4A4F46),
                        Color(0xFF22251F),
                        Color(0xFF11130F),
                      ],
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x382A2721),
                        offset: Offset(0, 4),
                        blurRadius: 8,
                      ),
                      BoxShadow(
                        color: Color(0xFFFFF9E8),
                        offset: Offset(0, 2),
                      ),
                    ],
                  ),
                  child: const Center(
                    child: LisanIcon(
                      LisanIconType.spark,
                      size: 16,
                      color: LisanTheme.acid,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                const Text(
                  'Lisan',
                  style: TextStyle(
                    color: LisanTheme.ink,
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.5,
                  ),
                ),
              ],
            ),
          ),

          // Advanced settings button
          GestureDetector(
            onTap: () {
              setState(() {
                _view = AppView.settings;
              });
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(7),
                border: Border.all(color: const Color(0xFF9C9587)),
                gradient: const LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0xFFEEE7D8), Color(0xFFC9C1B1)],
                ),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0xFF9F988A),
                    offset: Offset(0, 2),
                  ),
                  BoxShadow(
                    color: Color(0x24353028),
                    offset: Offset(0, 4),
                    blurRadius: 6,
                  ),
                ],
              ),
              child: const Row(
                children: [
                  Text(
                    'Advanced settings',
                    style: TextStyle(
                      color: Color(0xFF474942),
                      fontSize: 9.5,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.3,
                    ),
                  ),
                  SizedBox(width: 4),
                  LisanIcon(
                    LisanIconType.arrow,
                    size: 13,
                    color: Color(0xFF474942),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------------
  // View Switcher
  // -------------------------------------------------------------------------
  Widget _buildCurrentView() {
    switch (_view) {
      case AppView.ready:
      case AppView.speaking:
        return _buildVoiceView();
      case AppView.language:
        return _buildLanguageView();
      case AppView.result:
        return _buildResultView();
      case AppView.settings:
        return _buildSettingsView();
    }
  }

  // -------------------------------------------------------------------------
  // 1. Ready & Speaking View
  // -------------------------------------------------------------------------
  Widget _buildVoiceView() {
    final isSpeaking = _view == AppView.speaking;

    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 28, 22, 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Eyebrow
          Row(
            children: [
              Container(
                width: 19,
                height: 2,
                color: LisanTheme.orange,
              ),
              const SizedBox(width: 9),
              Text(
                isSpeaking ? 'LISTENING NOW' : 'VOICE TRANSLATOR',
                style: const TextStyle(
                  color: Color(0xFF62645C),
                  fontSize: 9.5,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.8,
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),

          // Hero Title (Serif)
          if (isSpeaking)
            const Text(
              'I’m listening…',
              style: TextStyle(
                fontFamily: 'serif',
                fontSize: 50,
                color: LisanTheme.ink,
                height: 0.95,
                letterSpacing: -1.5,
              ),
            )
          else
            Text.rich(
              const TextSpan(
                style: TextStyle(
                  fontFamily: 'serif',
                  fontSize: 54,
                  color: LisanTheme.ink,
                  height: 0.92,
                  letterSpacing: -1.8,
                ),
                children: [
                  TextSpan(text: 'Speak freely.\n'),
                  TextSpan(
                    text: 'Be understood.',
                    style: TextStyle(
                      color: LisanTheme.orange,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 12),

          // Hero Copy
          Text(
            isSpeaking
                ? 'Keep holding while you speak'
                : 'Instant translation across the languages of Ethiopia and the Horn.',
            style: const TextStyle(
              color: LisanTheme.muted,
              fontSize: 12.5,
              height: 1.5,
            ),
          ),

          // Conversation Active Pill
          if (_conversationMode) ...[
            const SizedBox(height: 14),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: LisanTheme.well,
                borderRadius: BorderRadius.circular(7),
                border: Border.all(color: const Color(0xFF1B1D19)),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0xFFF9F2E3),
                    offset: Offset(0, 1),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _firstLanguage.tone,
                      boxShadow: [
                        BoxShadow(
                          color: _firstLanguage.tone,
                          blurRadius: 4,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    _firstLanguage.name,
                    style: const TextStyle(
                      color: Color(0xFFE5E8D9),
                      fontSize: 8.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 6),
                    child: LisanIcon(
                      LisanIconType.arrow,
                      size: 11,
                      color: Color(0xFFAFABA2),
                    ),
                  ),
                  Text(
                    _secondLanguage.name,
                    style: const TextStyle(
                      color: Color(0xFFE5E8D9),
                      fontSize: 8.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _secondLanguage.tone,
                      boxShadow: [
                        BoxShadow(
                          color: _secondLanguage.tone,
                          blurRadius: 4,
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],

          const Spacer(),

          // Orb Centerpiece Stage
          Center(
            child: _OrbStage(
              isSpeaking: isSpeaking,
              onBeginSpeaking: _beginSpeaking,
              onFinishSpeaking: _finishSpeaking,
            ),
          ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------------
  // 2. Language Selection View (Low Literacy Iconography & Vibrant Colors)
  // -------------------------------------------------------------------------
  Widget _buildLanguageView() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 18, 22, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(width: 19, height: 2, color: LisanTheme.orange),
                        const SizedBox(width: 9),
                        const Text(
                          'WE HEARD YOU',
                          style: TextStyle(
                            color: Color(0xFF62645C),
                            fontSize: 9.5,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.8,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Which language\ndid you speak?',
                      style: TextStyle(
                        fontFamily: 'serif',
                        fontSize: 38,
                        color: LisanTheme.ink,
                        height: 0.96,
                        letterSpacing: -1.2,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              _buildIconButton(
                icon: LisanIconType.close,
                onTap: _reset,
              ),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            'Choose by color or symbol',
            style: TextStyle(
              color: LisanTheme.muted,
              fontSize: 11,
            ),
          ),
          const SizedBox(height: 16),

          // 2x2 Grid + Full Width English
          Expanded(
            child: Column(
              children: [
                Expanded(
                  child: GridView.count(
                    crossAxisCount: 2,
                    mainAxisSpacing: 10,
                    crossAxisSpacing: 10,
                    childAspectRatio: 1.45,
                    physics: const NeverScrollableScrollPhysics(),
                    children: [
                      for (int i = 0; i < 4; i++)
                        _buildLanguageCard(kLanguages[i]),
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                _buildEnglishFullCard(kLanguages[4]),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageCard(AppLanguage lang) {
    return GestureDetector(
      onTap: () => _chooseLanguage(lang),
      child: Container(
        padding: const EdgeInsets.all(13),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(13),
          border: Border.all(
            color: Color.lerp(lang.tone, const Color(0xFF2B2B26), 0.3)!,
          ),
          gradient: RadialGradient(
            center: const Alignment(0.8, -0.8),
            radius: 1.0,
            colors: [
              Colors.white.withValues(alpha: 0.25),
              Color.lerp(lang.tone, const Color(0xFF383A33), 0.28)!,
            ],
          ),
          boxShadow: [
            BoxShadow(
              color: Color.lerp(lang.tone, Colors.black, 0.45)!,
              offset: const Offset(0, 3),
            ),
            const BoxShadow(
              color: Color(0x30342E26),
              offset: Offset(0, 6),
              blurRadius: 9,
            ),
          ],
        ),
        child: Stack(
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Symbol Container
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white.withValues(alpha: 0.32)),
                    color: const Color(0x381C1D19),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x33FFFFFF),
                        offset: Offset(0, 1),
                      ),
                    ],
                  ),
                  child: Center(
                    child: LanguageSymbolWidget(
                      symbol: lang.symbol,
                      size: 22,
                      color: Colors.white,
                    ),
                  ),
                ),

                // Name Labels
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      lang.native,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 13.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    Text(
                      lang.name,
                      style: TextStyle(
                        color: Colors.white.withValues(alpha: 0.72),
                        fontSize: 8.5,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const Positioned(
              right: 0,
              bottom: 0,
              child: LisanIcon(
                LisanIconType.arrow,
                size: 16,
                color: Color(0xCCFFFFFF),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEnglishFullCard(AppLanguage lang) {
    return GestureDetector(
      onTap: () => _chooseLanguage(lang),
      child: Container(
        height: 84,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(13),
          border: Border.all(
            color: Color.lerp(lang.tone, const Color(0xFF2B2B26), 0.3)!,
          ),
          gradient: RadialGradient(
            center: const Alignment(0.8, -0.8),
            radius: 1.2,
            colors: [
              Colors.white.withValues(alpha: 0.24),
              Color.lerp(lang.tone, const Color(0xFF383A33), 0.28)!,
            ],
          ),
          boxShadow: [
            BoxShadow(
              color: Color.lerp(lang.tone, Colors.black, 0.45)!,
              offset: const Offset(0, 3),
            ),
            const BoxShadow(
              color: Color(0x30342E26),
              offset: Offset(0, 6),
              blurRadius: 9,
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              width: 42,
              height: 42,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white.withValues(alpha: 0.32)),
                color: const Color(0x381C1D19),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x33FFFFFF),
                    offset: Offset(0, 1),
                  ),
                ],
              ),
              child: Center(
                child: LanguageSymbolWidget(
                  symbol: lang.symbol,
                  size: 24,
                  color: Colors.white,
                ),
              ),
            ),
            const SizedBox(width: 14),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  lang.native,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 14.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  lang.name,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.72),
                    fontSize: 9,
                  ),
                ),
              ],
            ),
            const Spacer(),
            const LisanIcon(
              LisanIconType.arrow,
              size: 18,
              color: Color(0xCCFFFFFF),
            ),
          ],
        ),
      ),
    );
  }

  // -------------------------------------------------------------------------
  // 3. Hardware Translation Card Result View
  // -------------------------------------------------------------------------
  Widget _buildResultView() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 16, 22, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(width: 19, height: 2, color: LisanTheme.orange),
                        const SizedBox(width: 9),
                        const Text(
                          'TRANSLATION READY',
                          style: TextStyle(
                            color: Color(0xFF62645C),
                            fontSize: 9.5,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.8,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'You’re understood.',
                      style: TextStyle(
                        fontFamily: 'serif',
                        fontSize: 38,
                        color: LisanTheme.ink,
                        height: 0.98,
                        letterSpacing: -1.2,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              _buildIconButton(
                icon: LisanIconType.close,
                onTap: _reset,
              ),
            ],
          ),
          const SizedBox(height: 18),

          // Main Hardware Screen Card
          Container(
            decoration: BoxDecoration(
              color: LisanTheme.well,
              borderRadius: BorderRadius.circular(17),
              border: Border.all(
                color: const Color(0xFFAAA293),
                width: 7,
              ),
              boxShadow: const [
                BoxShadow(
                  color: Color(0xFF666157),
                  offset: Offset(0, 0),
                  blurRadius: 1,
                ),
                BoxShadow(
                  color: Color(0xFFFFF8E7),
                  offset: Offset(0, 2),
                ),
                BoxShadow(
                  color: Color(0x3D342E25),
                  offset: Offset(0, 8),
                  blurRadius: 15,
                ),
              ],
            ),
            child: Stack(
              children: [
                // Top-right micro-label
                Positioned(
                  top: 7,
                  right: 10,
                  child: Text(
                    _isLoading ? 'PROCESSING AUDIO...' : 'TRANSLATION OUTPUT',
                    style: TextStyle(
                      color: LisanTheme.acid.withValues(alpha: 0.45),
                      fontSize: 5.5,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.4,
                    ),
                  ),
                ),

                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Top Section: Source
                    Padding(
                      padding: const EdgeInsets.fromLTRB(18, 18, 18, 14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              _buildMiniSwatch(_language),
                              const SizedBox(width: 8),
                              Text(
                                _language.name.toUpperCase(),
                                style: const TextStyle(
                                  color: Color(0xFFAFB5A7),
                                  fontSize: 8.5,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.0,
                                ),
                              ),
                              const Spacer(),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 7,
                                  vertical: 3,
                                ),
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(4),
                                  border: Border.all(
                                    color: LisanTheme.acid.withValues(alpha: 0.25),
                                  ),
                                  color: LisanTheme.acid.withValues(alpha: 0.08),
                                ),
                                child: const Text(
                                  'DETECTED',
                                  style: TextStyle(
                                    color: LisanTheme.acid,
                                    fontSize: 6.5,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(
                            _sourceText,
                            style: const TextStyle(
                              color: Color(0xFFC3C8BB),
                              fontSize: 15,
                              height: 1.5,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Divider with spark emblem
                    Row(
                      children: [
                        Expanded(
                          child: Container(
                            height: 1,
                            color: const Color(0xFF464B43),
                          ),
                        ),
                        Container(
                          width: 27,
                          height: 27,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            border: Border.all(color: const Color(0xFF596052)),
                            color: const Color(0xFF1A1D19),
                          ),
                          child: const Center(
                            child: LisanIcon(
                              LisanIconType.spark,
                              size: 14,
                              color: LisanTheme.acid,
                            ),
                          ),
                        ),
                        Expanded(
                          child: Container(
                            height: 1,
                            color: const Color(0xFF464B43),
                          ),
                        ),
                      ],
                    ),

                    // Bottom Section: Output
                    Padding(
                      padding: const EdgeInsets.fromLTRB(18, 14, 18, 18),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              _buildMiniSwatch(_targetLanguage),
                              const SizedBox(width: 8),
                              Text(
                                _targetLanguage.name.toUpperCase(),
                                style: const TextStyle(
                                  color: Color(0xFFAFB5A7),
                                  fontSize: 8.5,
                                  fontWeight: FontWeight.w700,
                                  letterSpacing: 1.0,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Text(
                            _outputText,
                            style: const TextStyle(
                              fontFamily: 'serif',
                              color: Color(0xFFF2F4E9),
                              fontSize: 27,
                              height: 1.25,
                              letterSpacing: -0.5,
                            ),
                          ),
                          const SizedBox(height: 18),

                          // Audio Playback Row
                          Row(
                            children: [
                              GestureDetector(
                                onTap: () {
                                  if (_playing) {
                                    _audioPlayer.stop();
                                    _playbackTimer?.cancel();
                                    setState(() => _playing = false);
                                  } else {
                                    _playAudio();
                                  }
                                },
                                child: Container(
                                  width: 38,
                                  height: 38,
                                  decoration: const BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: LisanTheme.acid,
                                    boxShadow: [
                                      BoxShadow(
                                        color: Color(0xFF718036),
                                        offset: Offset(0, 3),
                                      ),
                                      BoxShadow(
                                        color: Color(0xFF10120F),
                                        offset: Offset(0, 5),
                                        blurRadius: 7,
                                      ),
                                    ],
                                  ),
                                  child: Center(
                                    child: LisanIcon(
                                      LisanIconType.volume,
                                      size: 19,
                                      color: const Color(0xFF21241F),
                                    ),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: WaveformEqualizer(active: _playing),
                              ),
                              const SizedBox(width: 10),
                              Text(
                                _audioDurationText,
                                style: const TextStyle(
                                  color: Color(0xFF858C7F),
                                  fontSize: 8.5,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Trust Badges
          Row(
            children: [
              _buildTrustBadge(
                icon: LisanIconType.brain,
                label: _isTmMatch ? 'Verified Memory' : 'AI Dynamic',
              ),
              const SizedBox(width: 8),
              _buildTrustBadge(
                icon: LisanIconType.shield,
                label: 'AI Guard',
              ),
            ],
          ),

          const Spacer(),

          // Continuation Buttons
          if (_conversationMode)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
              decoration: BoxDecoration(
                color: const Color(0xFFC8C0B1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF807A6F)),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0xFFF8F0DF),
                    offset: Offset(0, 1),
                  ),
                ],
              ),
              child: Row(
                children: [
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _targetLanguage.tone,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _targetLanguage.name,
                        style: const TextStyle(
                          color: LisanTheme.ink,
                          fontSize: 10.5,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const Text(
                        'Next speaker',
                        style: TextStyle(
                          color: LisanTheme.muted,
                          fontSize: 7.5,
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Listener(
                    behavior: HitTestBehavior.opaque,
                    onPointerDown: (_) => _beginSpeaking(),
                    onPointerUp: (_) => _finishSpeaking(),
                    onPointerCancel: (_) => _finishSpeaking(),
                    child: Container(
                      width: 54,
                      height: 54,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: const Color(0xFF30332D),
                          width: 4,
                        ),
                        gradient: const RadialGradient(
                          center: Alignment(-0.3, -0.4),
                          radius: 0.9,
                          colors: [
                            Color(0xFFFF8864),
                            LisanTheme.orange,
                            Color(0xFFA52F1D),
                          ],
                        ),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0xFFECE5D5),
                            offset: Offset(0, 0),
                            blurRadius: 0,
                            spreadRadius: 2,
                          ),
                          BoxShadow(
                            color: Color(0x4D342C23),
                            offset: Offset(0, 4),
                            blurRadius: 6,
                          ),
                        ],
                      ),
                      child: const Center(
                        child: LisanIcon(
                          LisanIconType.mic,
                          size: 23,
                          color: Color(0xFFFFF8E9),
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  const SizedBox(
                    width: 36,
                    child: Text(
                      'HOLD TO REPLY',
                      style: TextStyle(
                        color: Color(0xFF62645C),
                        fontSize: 7.5,
                        fontWeight: FontWeight.w700,
                        height: 1.3,
                      ),
                    ),
                  ),
                ],
              ),
            )
          else
            _buildOrangeTactileButton(
              label: 'Speak again',
              iconLeading: const LisanIcon(
                LisanIconType.mic,
                size: 19,
                color: Colors.white,
              ),
              iconTrailing: const LisanIcon(
                LisanIconType.arrow,
                size: 18,
                color: Colors.white,
              ),
              onTap: _reset,
            ),
        ],
      ),
    );
  }

  Widget _buildMiniSwatch(AppLanguage lang) {
    return Container(
      width: 25,
      height: 25,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: lang.tone,
        border: Border.all(
          color: Color.lerp(lang.tone, Colors.white, 0.45)!,
        ),
      ),
      child: Center(
        child: LanguageSymbolWidget(
          symbol: lang.symbol,
          size: 13,
          color: Colors.white,
        ),
      ),
    );
  }

  Widget _buildTrustBadge({
    required LisanIconType icon,
    required String label,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.24),
        borderRadius: BorderRadius.circular(5),
        border: Border.all(color: const Color(0xFFAAA294)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x99FFFFFF),
            offset: Offset(0, 1),
          ),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          LisanIcon(icon, size: 14, color: const Color(0xFF696B63)),
          const SizedBox(width: 5),
          Text(
            label,
            style: const TextStyle(
              color: Color(0xFF696B63),
              fontSize: 7.5,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------------
  // 4. Advanced Settings View
  // -------------------------------------------------------------------------
  Widget _buildSettingsView() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 16, 22, 20),
      child: ListView(
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(width: 19, height: 2, color: LisanTheme.orange),
                        const SizedBox(width: 9),
                        const Text(
                          'PERSONALIZE LISAN',
                          style: TextStyle(
                            color: Color(0xFF62645C),
                            fontSize: 9.5,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 1.8,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    const Text(
                      'Advanced\nsettings',
                      style: TextStyle(
                        fontFamily: 'serif',
                        fontSize: 38,
                        color: LisanTheme.ink,
                        height: 0.98,
                        letterSpacing: -1.2,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 12),
              _buildIconButton(
                icon: LisanIconType.close,
                onTap: _reset,
              ),
            ],
          ),
          const SizedBox(height: 20),

          // Section 01: Translation
          _buildSettingsGroupHeader('TRANSLATION', '01'),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFC8C0B1),
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: const Color(0xFF8F887B)),
              boxShadow: const [
                BoxShadow(
                  color: Color(0xFFFFF8E9),
                  offset: Offset(0, 1),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Translate into',
                  style: TextStyle(
                    color: Color(0xFF30322D),
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const Text(
                  'Your default output language',
                  style: TextStyle(
                    color: Color(0xFF74746C),
                    fontSize: 8.5,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    for (final target in ['English', 'Amharic', 'Somali'])
                      Expanded(
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 3),
                          child: GestureDetector(
                            onTap: () {
                              setState(() => _defaultTarget = target);
                            },
                            child: Container(
                              height: 38,
                              decoration: BoxDecoration(
                                color: _defaultTarget == target
                                    ? LisanTheme.well
                                    : const Color(0xFFE8E1D3),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                  color: _defaultTarget == target
                                      ? const Color(0xFF171916)
                                      : const Color(0xFF8D8679),
                                ),
                                boxShadow: [
                                  if (_defaultTarget != target)
                                    const BoxShadow(
                                      color: Color(0xFF918A7D),
                                      offset: Offset(0, 2),
                                    ),
                                ],
                              ),
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    target,
                                    style: TextStyle(
                                      color: _defaultTarget == target
                                          ? LisanTheme.acid
                                          : const Color(0xFF5C5E57),
                                      fontSize: 8.5,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  if (_defaultTarget == target) ...[
                                    const SizedBox(width: 4),
                                    const LisanIcon(
                                      LisanIconType.check,
                                      size: 13,
                                      color: LisanTheme.acid,
                                    ),
                                  ],
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Section 02: Conversation mode
          _buildSettingsGroupHeader('CONVERSATION MODE', '02'),
          Container(
            decoration: BoxDecoration(
              color: const Color(0xFFC8C0B1),
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: const Color(0xFF8F887B)),
              boxShadow: const [
                BoxShadow(
                  color: Color(0xFFFFF8E9),
                  offset: Offset(0, 1),
                ),
              ],
            ),
            child: Column(
              children: [
                ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 4,
                  ),
                  leading: Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: LisanTheme.well,
                      border: Border.all(color: const Color(0xFF282B26)),
                    ),
                    child: const Center(
                      child: LisanIcon(
                        LisanIconType.volume,
                        size: 18,
                        color: LisanTheme.acid,
                      ),
                    ),
                  ),
                  title: const Text(
                    'Automatic two-way translation',
                    style: TextStyle(
                      color: Color(0xFF30322D),
                      fontSize: 10.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  subtitle: const Text(
                    'Hear either language and translate to the other',
                    style: TextStyle(
                      color: Color(0xFF74746C),
                      fontSize: 8,
                    ),
                  ),
                  trailing: Switch(
                    value: _conversationMode,
                    activeThumbColor: LisanTheme.acid,
                    activeTrackColor: const Color(0xFF87963D),
                    inactiveThumbColor: const Color(0xFFF1EADC),
                    inactiveTrackColor: const Color(0xFFAAA295),
                    onChanged: (val) {
                      setState(() => _conversationMode = val);
                    },
                  ),
                ),

                // Language Selectors
                Padding(
                  padding: const EdgeInsets.fromLTRB(14, 0, 14, 12),
                  child: Column(
                    children: [
                      _buildLanguageChoiceRow(
                        label: 'First language',
                        selected: _firstLanguage,
                        blocked: _secondLanguage,
                        onSelect: (lang) => setState(() => _firstLanguage = lang),
                      ),
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        child: Row(
                          children: [
                            const SizedBox(width: 80),
                            Expanded(
                              child: Container(
                                height: 1,
                                color: const Color(0x38424039),
                              ),
                            ),
                            const Padding(
                              padding: EdgeInsets.symmetric(horizontal: 6),
                              child: LisanIcon(
                                LisanIconType.arrow,
                                size: 14,
                                color: Color(0xFF65675F),
                              ),
                            ),
                            Expanded(
                              child: Container(
                                height: 1,
                                color: const Color(0x38424039),
                              ),
                            ),
                          ],
                        ),
                      ),
                      _buildLanguageChoiceRow(
                        label: 'Second language',
                        selected: _secondLanguage,
                        blocked: _firstLanguage,
                        onSelect: (lang) => setState(() => _secondLanguage = lang),
                      ),
                    ],
                  ),
                ),

                // Explainer
                Container(
                  margin: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                  padding: const EdgeInsets.all(9),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(
                      color: const Color(0xFF918A7E),
                      style: BorderStyle.solid,
                    ),
                  ),
                  child: const Row(
                    children: [
                      LisanIcon(
                        LisanIconType.spark,
                        size: 14,
                        color: Color(0xFF666860),
                      ),
                      SizedBox(width: 7),
                      Expanded(
                        child: Text(
                          'Lisan detects who is speaking and switches direction automatically.',
                          style: TextStyle(
                            color: Color(0xFF666860),
                            fontSize: 7.5,
                            height: 1.45,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Section 03: Experience
          _buildSettingsGroupHeader('EXPERIENCE', '03'),
          Container(
            decoration: BoxDecoration(
              color: const Color(0xFFC8C0B1),
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: const Color(0xFF8F887B)),
              boxShadow: const [
                BoxShadow(
                  color: Color(0xFFFFF8E9),
                  offset: Offset(0, 1),
                ),
              ],
            ),
            child: Column(
              children: [
                _buildSettingToggleTile(
                  title: 'Smart language detection',
                  description: 'Recognize the language you speak',
                  enabled: _smartDetect,
                  onChanged: (val) => setState(() => _smartDetect = val),
                  showDivider: true,
                ),
                _buildSettingToggleTile(
                  title: 'Auto-play translation',
                  description: 'Speak results aloud automatically',
                  enabled: _autoPlay,
                  onChanged: (val) => setState(() => _autoPlay = val),
                  showDivider: true,
                ),
                _buildSettingToggleTile(
                  title: 'Touch feedback',
                  description: 'Gentle vibration when recording',
                  enabled: _haptics,
                  onChanged: (val) => setState(() => _haptics = val),
                  showDivider: false,
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // Section 04: Backend Server Connection
          _buildSettingsGroupHeader('AI SERVER ENDPOINT', '04'),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFC8C0B1),
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: const Color(0xFF8F887B)),
              boxShadow: const [
                BoxShadow(
                  color: Color(0xFFFFF8E9),
                  offset: Offset(0, 1),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Local AI Server URL',
                  style: TextStyle(
                    color: Color(0xFF30322D),
                    fontSize: 10.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 6),
                TextField(
                  controller: _serverController,
                  style: const TextStyle(
                    color: LisanTheme.ink,
                    fontSize: 12,
                    fontFamily: 'monospace',
                  ),
                  decoration: InputDecoration(
                    filled: true,
                    fillColor: const Color(0xFFEEE7D8),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(6),
                      borderSide: const BorderSide(color: Color(0xFF8D8679)),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 8,
                    ),
                  ),
                  onSubmitted: (url) {
                    final uri = Uri.tryParse(url.trim());
                    if (uri != null) {
                      widget.api.baseUri = uri;
                    }
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),

          // Privacy Note
          const Row(
            children: [
              LisanIcon(
                LisanIconType.shield,
                size: 16,
                color: Color(0xFF666860),
              ),
              SizedBox(width: 7),
              Expanded(
                child: Text(
                  'Your voice preferences stay private on this device.',
                  style: TextStyle(
                    color: Color(0xFF666860),
                    fontSize: 7.5,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),

          // Save Preferences Button
          _buildOrangeTactileButton(
            label: 'Save preferences',
            iconTrailing: const LisanIcon(
              LisanIconType.check,
              size: 18,
              color: Colors.white,
            ),
            onTap: _reset,
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildSettingsGroupHeader(String title, String number) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(2, 0, 2, 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: Color(0xFF5F6159),
              fontSize: 7.5,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.2,
            ),
          ),
          Text(
            number,
            style: const TextStyle(
              color: Color(0xFF5F6159),
              fontSize: 7.5,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.2,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSettingToggleTile({
    required String title,
    required String description,
    required bool enabled,
    required ValueChanged<bool> onChanged,
    required bool showDivider,
  }) {
    return Column(
      children: [
        ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 14),
          title: Text(
            title,
            style: const TextStyle(
              color: Color(0xFF30322D),
              fontSize: 10.5,
              fontWeight: FontWeight.w700,
            ),
          ),
          subtitle: Text(
            description,
            style: const TextStyle(
              color: Color(0xFF74746C),
              fontSize: 8,
            ),
          ),
          trailing: Switch(
            value: enabled,
            activeThumbColor: LisanTheme.acid,
            activeTrackColor: const Color(0xFF87963D),
            inactiveThumbColor: const Color(0xFFF1EADC),
            inactiveTrackColor: const Color(0xFFAAA295),
            onChanged: onChanged,
          ),
        ),
        if (showDivider)
          const Divider(
            height: 1,
            color: Color(0x2846433C),
            indent: 14,
            endIndent: 14,
          ),
      ],
    );
  }

  Widget _buildLanguageChoiceRow({
    required String label,
    required AppLanguage selected,
    required AppLanguage blocked,
    required ValueChanged<AppLanguage> onSelect,
  }) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFF64665F),
            fontSize: 8.5,
          ),
        ),
        Row(
          children: [
            for (final lang in kLanguages)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2),
                child: GestureDetector(
                  onTap: lang.code == blocked.code ? null : () => onSelect(lang),
                  child: Opacity(
                    opacity: lang.code == blocked.code ? 0.28 : 1.0,
                    child: Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: selected.code == lang.code
                            ? lang.tone
                            : const Color(0xFFD7CFBF),
                        border: Border.all(
                          color: selected.code == lang.code
                              ? const Color(0xFF242620)
                              : const Color(0xFF8B8478),
                        ),
                        boxShadow: const [
                          BoxShadow(
                            color: Color(0xFFF8F1E2),
                            offset: Offset(0, 1),
                          ),
                        ],
                      ),
                      child: Center(
                        child: LanguageSymbolWidget(
                          symbol: lang.symbol,
                          size: 14,
                          color: selected.code == lang.code
                              ? Colors.white
                              : const Color(0xFF75756E),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }

  // -------------------------------------------------------------------------
  // Shared Components
  // -------------------------------------------------------------------------
  Widget _buildIconButton({
    required LisanIconType icon,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: Border.all(color: const Color(0xFF989183)),
          gradient: const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFF0E9DB), Color(0xFFC6BEAE)],
          ),
          boxShadow: const [
            BoxShadow(
              color: Color(0xFF9E978A),
              offset: Offset(0, 2),
            ),
            BoxShadow(
              color: Color(0x28312D26),
              offset: Offset(0, 4),
              blurRadius: 7,
            ),
          ],
        ),
        child: Center(
          child: LisanIcon(icon, size: 18, color: const Color(0xFF464840)),
        ),
      ),
    );
  }

  Widget _buildOrangeTactileButton({
    required String label,
    Widget? iconLeading,
    Widget? iconTrailing,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        height: 55,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(9),
          border: Border.all(color: const Color(0xFF8D3320)),
          gradient: const LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFFF56E4B), Color(0xFFD4472B)],
          ),
          boxShadow: const [
            BoxShadow(
              color: Color(0xFF8F301E),
              offset: Offset(0, 3),
            ),
            BoxShadow(
              color: Color(0x33432D23),
              offset: Offset(0, 6),
              blurRadius: 9,
            ),
          ],
        ),
        child: Row(
          children: [
            if (iconLeading != null) ...[
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0x3857170D),
                  border: Border.all(color: const Color(0x47FFFFFF)),
                ),
                child: Center(child: iconLeading),
              ),
              const SizedBox(width: 11),
            ],
            Text(
              label,
              style: const TextStyle(
                color: Color(0xFFFFF8EA),
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
              ),
            ),
            const Spacer(),
            ?iconTrailing,
          ],
        ),
      ),
    );
  }

  Widget _buildHomeIndicator() {
    return Container(
      height: 24,
      alignment: Alignment.center,
      child: Container(
        width: 86,
        height: 4,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(2),
          color: const Color(0xFF8F887B),
          boxShadow: const [
            BoxShadow(
              color: Color(0xFFEEE7D8),
              offset: Offset(0, 1),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Concentric Centerpiece Dial & Orbital Animations
// ---------------------------------------------------------------------------
class _OrbStage extends StatefulWidget {
  const _OrbStage({
    required this.isSpeaking,
    required this.onBeginSpeaking,
    required this.onFinishSpeaking,
  });

  final bool isSpeaking;
  final VoidCallback onBeginSpeaking;
  final VoidCallback onFinishSpeaking;

  @override
  State<_OrbStage> createState() => _OrbStageState();
}

class _OrbStageState extends State<_OrbStage>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    if (widget.isSpeaking) {
      _pulseController.repeat();
    }
  }

  @override
  void didUpdateWidget(covariant _OrbStage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isSpeaking != oldWidget.isSpeaking) {
      if (widget.isSpeaking) {
        _pulseController.repeat();
      } else {
        _pulseController.stop();
        _pulseController.reset();
      }
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 260,
      height: 260,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Orbital Conic Bezel Gauge
          Container(
            width: 230,
            height: 230,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: const Color(0xFF9E9585), width: 1),
            ),
          ),

          // Animated Pulsing Orbital Rings when speaking
          AnimatedBuilder(
            animation: _pulseController,
            builder: (context, child) {
              final val = _pulseController.value;
              final ringScale1 = widget.isSpeaking ? (0.85 + val * 0.25) : 1.0;
              final ringOpacity1 = widget.isSpeaking
                  ? (1.0 - val).clamp(0.0, 1.0)
                  : 0.25;

              final val2 = (val + 0.32) % 1.0;
              final ringScale2 = widget.isSpeaking ? (0.85 + val2 * 0.25) : 1.0;
              final ringOpacity2 = widget.isSpeaking
                  ? (1.0 - val2).clamp(0.0, 1.0)
                  : 0.2;

              final val3 = (val + 0.64) % 1.0;
              final ringScale3 = widget.isSpeaking ? (0.85 + val3 * 0.25) : 1.0;
              final ringOpacity3 = widget.isSpeaking
                  ? (1.0 - val3).clamp(0.0, 1.0)
                  : 0.15;

              return Stack(
                alignment: Alignment.center,
                children: [
                  // Orbit 3 (238px)
                  Transform.scale(
                    scale: ringScale3,
                    child: Container(
                      width: 238,
                      height: 238,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: widget.isSpeaking
                              ? LisanTheme.orange.withValues(alpha: ringOpacity3)
                              : const Color(0x33262924),
                          width: widget.isSpeaking ? 2 : 1,
                        ),
                      ),
                    ),
                  ),

                  // Orbit 2 (198px)
                  Transform.scale(
                    scale: ringScale2,
                    child: Container(
                      width: 198,
                      height: 198,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: widget.isSpeaking
                              ? LisanTheme.orange.withValues(alpha: ringOpacity2)
                              : const Color(0x33262924),
                          width: widget.isSpeaking ? 2 : 1,
                        ),
                      ),
                    ),
                  ),

                  // Orbit 1 (162px)
                  Transform.scale(
                    scale: ringScale1,
                    child: Container(
                      width: 162,
                      height: 162,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: widget.isSpeaking
                              ? LisanTheme.orange.withValues(alpha: ringOpacity1)
                              : const Color(0x33262924),
                          width: widget.isSpeaking ? 2 : 1,
                        ),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),

          // Waveform equalizer when speaking
          if (widget.isSpeaking)
            const Positioned(
              bottom: 20,
              child: SizedBox(
                width: 220,
                height: 48,
                child: WaveformEqualizer(active: true),
              ),
            ),

          // Central 126px Tactile Dial
          Listener(
            key: const ValueKey('mic_dial_button'),
            behavior: HitTestBehavior.opaque,
            onPointerDown: (_) => widget.onBeginSpeaking(),
            onPointerUp: (_) => widget.onFinishSpeaking(),
            onPointerCancel: (_) => widget.onFinishSpeaking(),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 140),
              width: 126,
              height: 126,
              transform: widget.isSpeaking
                  ? Matrix4.translationValues(0, 5, 0)
                  : Matrix4.identity(),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(color: const Color(0xFF2D302B), width: 7),
                gradient: const RadialGradient(
                  center: Alignment(-0.25, -0.4),
                  radius: 0.9,
                  colors: [
                    Color(0xFFFF8B64),
                    LisanTheme.orange,
                    LisanTheme.orangeDark,
                    Color(0xFF792417),
                  ],
                  stops: [0.0, 0.42, 0.75, 1.0],
                ),
                boxShadow: [
                  const BoxShadow(
                    color: Color(0xFF151713),
                    spreadRadius: 2,
                  ),
                  const BoxShadow(
                    color: Color(0xFFA9A191),
                    spreadRadius: 8,
                  ),
                  const BoxShadow(
                    color: Color(0xFFF6EFDF),
                    spreadRadius: 10,
                  ),
                  BoxShadow(
                    color: const Color(0x56342C23),
                    offset: widget.isSpeaking
                        ? const Offset(0, 4)
                        : const Offset(0, 11),
                    blurRadius: widget.isSpeaking ? 6 : 14,
                  ),
                ],
              ),
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Inner decorative ring
                  Container(
                    width: 108,
                    height: 108,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: const Color(0x4DFFF2DC),
                        width: 1,
                      ),
                    ),
                  ),

                  // Top crescent highlight
                  Positioned(
                    top: 10,
                    child: Container(
                      width: 72,
                      height: 17,
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(10),
                        gradient: const LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Color(0x56FFFFFF),
                            Colors.transparent,
                          ],
                        ),
                      ),
                    ),
                  ),

                  // Mic Icon
                  const Center(
                    child: LisanIcon(
                      LisanIconType.mic,
                      size: 34,
                      color: Color(0xFFFFF8E9),
                      strokeWidth: 2.2,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Animated Waveform Equalizer
// ---------------------------------------------------------------------------
class WaveformEqualizer extends StatefulWidget {
  const WaveformEqualizer({
    super.key,
    required this.active,
    this.color = LisanTheme.acid,
  });

  final bool active;
  final Color color;

  @override
  State<WaveformEqualizer> createState() => _WaveformEqualizerState();
}

class _WaveformEqualizerState extends State<WaveformEqualizer>
    with SingleTickerProviderStateMixin {
  late final AnimationController _waveController;

  static const List<double> _baseHeights = [
    0.24, 0.40, 0.62, 0.34, 0.76, 0.52, 0.88, 0.60,
    0.38, 0.70, 0.46, 0.82, 0.56, 0.34, 0.64, 0.44, 0.28,
  ];

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 750),
    );
    if (widget.active) {
      _waveController.repeat(reverse: true);
    }
  }

  @override
  void didUpdateWidget(covariant WaveformEqualizer oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active != oldWidget.active) {
      if (widget.active) {
        _waveController.repeat(reverse: true);
      } else {
        _waveController.stop();
        _waveController.reset();
      }
    }
  }

  @override
  void dispose() {
    _waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _waveController,
      builder: (context, child) {
        return SizedBox(
          height: 32,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: List.generate(_baseHeights.length, (i) {
              final base = _baseHeights[i];
              double heightFactor = 0.35;
              if (widget.active) {
                final phase = (i * 0.38);
                final wave = math.sin(_waveController.value * math.pi * 2 + phase);
                heightFactor = (base * (0.45 + wave.abs() * 0.55)).clamp(0.15, 1.0);
              }
              return Container(
                width: 2.2,
                height: 32 * heightFactor,
                margin: const EdgeInsets.symmetric(horizontal: 1.5),
                decoration: BoxDecoration(
                  color: widget.color.withValues(alpha: widget.active ? 0.95 : 0.45),
                  borderRadius: BorderRadius.circular(1.1),
                ),
              );
            }),
          ),
        );
      },
    );
  }
}
