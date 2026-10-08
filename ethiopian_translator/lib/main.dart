import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;
import 'package:audioplayers/audioplayers.dart';
import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:path_provider/path_provider.dart';

import 'lisan_icons.dart';
import 'offline_nllb_translator.dart';
import 'offline_stt_service.dart';
import 'offline_translation_memory.dart';
import 'recording_service.dart';
import 'translator_api.dart';

String computeTtsCacheKey(String lang, String text) {
  final cleaned = text.trim();
  final hash = md5.convert(utf8.encode(cleaned)).toString().substring(0, 10);
  return '${lang}_$hash';
}

void main() => runApp(
  TranslatorApp(audioCapture: RecordingService(), api: TranslatorApi()),
);

class NativeTts {
  static const _channel = MethodChannel('com.example.ethiopian_translator/tts');

  static Future<bool> speak(String text, String lang) async {
    try {
      final res = await _channel.invokeMethod<bool>('speak', {
        'text': text,
        'lang': lang,
      });
      return res ?? false;
    } catch (e) {
      debugPrint('[NativeTts] error: $e');
      return false;
    }
  }

  static Future<void> stop() async {
    try {
      await _channel.invokeMethod('stop');
    } catch (_) {}
  }
}


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

enum AppView { ready, speaking, language, loading, result, settings }

// ---------------------------------------------------------------------------
// Root Application
// ---------------------------------------------------------------------------
class TranslatorApp extends StatelessWidget {
  const TranslatorApp({
    super.key,
    this.audioCapture,
    this.api,
    this.minHoldDuration = const Duration(milliseconds: 350),
  });

  final AudioCapture? audioCapture;
  final TranslatorApi? api;
  final Duration minHoldDuration;

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
      home: ConversationPage(
        audioCapture: audioCapture,
        api: api,
        minHoldDuration: minHoldDuration,
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Main Interactive View Container
// ---------------------------------------------------------------------------
class ConversationPage extends StatefulWidget {
  ConversationPage({
    super.key,
    AudioCapture? audioCapture,
    TranslatorApi? api,
    this.minHoldDuration = const Duration(milliseconds: 350),
  })  : audioCapture = audioCapture ?? RecordingService(),
        api = api ?? TranslatorApi();

  final AudioCapture audioCapture;
  final TranslatorApi api;
  final Duration minHoldDuration;

  @override
  State<ConversationPage> createState() => _ConversationPageState();
}

class _ConversationPageState extends State<ConversationPage>
    with TickerProviderStateMixin {
  AppView _view = AppView.ready;
  AppLanguage _language = kLanguages[0]; // Amharic
  AppLanguage _targetLanguage = kLanguages[4]; // Default partner: English
  bool _isEnglishSpeaker = true;

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
  String _sourceText = '';
  String _outputText = '';
  final String _audioDurationText = '0:00';
  String? _recordedFilePath;

  // ---------------------------------------------------------------------------
  // Offline Services
  // ---------------------------------------------------------------------------
  final OfflineSttService _offlineStt = OfflineSttService();
  final OfflineNllbTranslator _offlineNmt = OfflineNllbTranslator();
  bool _offlineReady = false;

  late final AudioPlayer _audioPlayer;
  late final TextEditingController _serverController;
  Timer? _playbackTimer;
  Timer? _initTimer;
  Timer? _personaTimer;

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

    // Fast instant launch: pre-warm NMT tokenizer gently in background AFTER first frame is drawn
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initTimer = Timer(const Duration(milliseconds: 600), () {
        if (mounted) _initTokenizerInBackground();
      });
    });

    _loadPersonaConfigAndPromptIfNeeded();
  }

  Future<void> _initTokenizerInBackground() async {
    try {
      debugPrint('[Offline] Background pre-warming NMT tokenizer...');
      await _offlineNmt.initializeTokenizer();
      if (mounted) setState(() => _offlineReady = true);
      debugPrint('[Offline] NMT tokenizer ready ✓');

      // Pre-warm STT session in the background so speech recognition is instantaneous
      Future.delayed(const Duration(milliseconds: 300), () async {
        try {
          debugPrint('[Offline] Pre-warming STT session in background...');
          await _offlineStt.initialize();
          debugPrint('[Offline] STT session ready ✓');

          // Pre-warm NMT sessions in background so translations are instantaneous with 0-second UI freeze
          Future.delayed(const Duration(milliseconds: 500), () async {
            try {
              debugPrint('[Offline] Pre-warming NMT model sessions in background...');
              await _offlineNmt.initialize();
              debugPrint('[Offline] NMT model sessions ready ✓');
            } catch (e) {
              debugPrint('[Offline] NMT pre-warm note: $e');
            }
          });
        } catch (e) {
          debugPrint('[Offline] STT pre-warm note: $e');
        }
      });
    } catch (e) {
      debugPrint('[Offline] Tokenizer background init error: $e');
    }
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    _serverController.dispose();
    _playbackTimer?.cancel();
    _initTimer?.cancel();
    _personaTimer?.cancel();
    _offlineStt.dispose();
    _offlineNmt.dispose();
    NativeTts.stop();
    super.dispose();
  }


  // -------------------------------------------------------------------------
  // Speaker Persona First-Launch Prompt & Persistence
  // -------------------------------------------------------------------------
  Future<File> _getConfigFile() async {
    final dir = await getApplicationDocumentsDirectory();
    return File('${dir.path}/lisan_persona_config.json');
  }

  Future<void> _loadPersonaConfigAndPromptIfNeeded() async {
    try {
      final file = await _getConfigFile();
      if (await file.exists()) {
        final content = await file.readAsString();
        final data = jsonDecode(content) as Map<String, dynamic>;
        final isEng = data['is_english_speaker'] as bool? ?? true;
        final partnerCode = data['partner_lang'] as String? ?? 'amh';
        final partner = kLanguages.firstWhere(
          (l) => l.backendKey == partnerCode,
          orElse: () => kLanguages[0],
        );
        if (mounted) {
          setState(() {
            _isEnglishSpeaker = isEng;
            _targetLanguage = partner;
          });
        }
      } else {
        // First launch! Prompt the user with the aesthetic alert box
        _personaTimer = Timer(const Duration(milliseconds: 250), () {
          if (mounted) {
            _showPersonaSetupDialog(canDismiss: false);
          }
        });
      }
    } catch (e) {
      debugPrint('Error loading persona config: $e');
    }
  }

  Future<void> _savePersonaConfig() async {
    try {
      final file = await _getConfigFile();
      final data = {
        'has_configured_persona': true,
        'is_english_speaker': _isEnglishSpeaker,
        'partner_lang': _targetLanguage.backendKey,
      };
      await file.writeAsString(jsonEncode(data));
    } catch (e) {
      debugPrint('Error saving persona config: $e');
    }
  }

  void _showPersonaSetupDialog({required bool canDismiss}) {
    showDialog(
      context: context,
      barrierDismissible: canDismiss,
      barrierColor: const Color(0xB80E100D),
      builder: (dialogCtx) {
        int dialogStep = 0; // 0: Question, 1: Partner selection (if YES)
        return PopScope(
          canPop: canDismiss,
          child: StatefulBuilder(
            builder: (ctx, setDialogState) {
              return Dialog(
                backgroundColor: Colors.transparent,
                insetPadding: const EdgeInsets.symmetric(
                  horizontal: 20,
                  vertical: 24,
                ),
                child: Container(
                  decoration: BoxDecoration(
                    color: LisanTheme.well,
                    borderRadius: BorderRadius.circular(22),
                    border: Border.all(
                      color: const Color(0xFFAAA293),
                      width: 3.5,
                    ),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x99000000),
                        offset: Offset(0, 14),
                        blurRadius: 35,
                      ),
                      BoxShadow(color: Color(0xFFFFF9EA), offset: Offset(0, 1)),
                    ],
                  ),
                  padding: const EdgeInsets.all(20),
                  child: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 200),
                    child: dialogStep == 0
                        ? _buildPersonaQuestionStep(
                            canDismiss: canDismiss,
                            onClose: () => Navigator.of(dialogCtx).pop(),
                            onYes: () {
                              setDialogState(() => dialogStep = 1);
                            },
                            onQetil: () {
                              Navigator.of(dialogCtx).pop();
                              setState(() {
                                _isEnglishSpeaker = false;
                                if (_targetLanguage.code == 'EN') {
                                  _targetLanguage = kLanguages[0];
                                }
                              });
                              _savePersonaConfig();
                            },
                          )
                        : _buildPartnerSelectionStep(
                            onBack: () => setDialogState(() => dialogStep = 0),
                            onSelectPartner: (lang) {
                              Navigator.of(dialogCtx).pop();
                              setState(() {
                                _isEnglishSpeaker = true;
                                _targetLanguage = lang;
                              });
                              _savePersonaConfig();
                            },
                          ),
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }

  Widget _buildPersonaQuestionStep({
    required bool canDismiss,
    required VoidCallback onClose,
    required VoidCallback onYes,
    required VoidCallback onQetil,
  }) {
    return Column(
      key: const ValueKey('step_question'),
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Micro-header
        Row(
          children: [
            Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF181B18),
                border: Border.all(color: const Color(0xFF3B4135)),
              ),
              child: const Center(
                child: LisanIcon(
                  LisanIconType.spark,
                  size: 12,
                  color: LisanTheme.acid,
                ),
              ),
            ),
            const SizedBox(width: 8),
            const Text(
              'LISAN / MODEL 01 · SYSTEM SETUP',
              style: TextStyle(
                color: Color(0xFF888B82),
                fontSize: 8,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.1,
              ),
            ),
            const Spacer(),
            if (canDismiss)
              GestureDetector(
                onTap: onClose,
                child: Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: const Color(0xFF1A1D1A),
                    border: Border.all(color: const Color(0xFF383D33)),
                  ),
                  child: const Center(
                    child: Icon(
                      Icons.close,
                      size: 13,
                      color: Color(0xFFC3C8BB),
                    ),
                  ),
                ),
              )
            else
              Container(
                width: 6,
                height: 6,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: LisanTheme.acid,
                  boxShadow: [BoxShadow(color: LisanTheme.acid, blurRadius: 4)],
                ),
              ),
          ],
        ),
        const SizedBox(height: 16),

        // Serif Title & Ge'ez
        const Text(
          'Are you an English speaker?',
          style: TextStyle(
            fontFamily: 'serif',
            fontSize: 25,
            color: Colors.white,
            height: 1.1,
            letterSpacing: -0.5,
          ),
        ),
        const SizedBox(height: 4),
        const Text(
          'እንግሊዝኛ ተናጋሪ ነዎት?',
          style: TextStyle(
            color: LisanTheme.orange,
            fontSize: 15,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 10),

        // Explanatory Micro-Copy
        const Text(
          'Select YES to translate between English and Ethiopian languages. Choose ቀጥል for local language translation only.',
          style: TextStyle(color: Color(0xFFA2A69A), fontSize: 11, height: 1.4),
        ),
        const SizedBox(height: 4),
        const Text(
          'የአገር ውስጥ ቋንቋዎችን ብቻ ለመተርጎም «ቀጥል»ን ይጫኑ።',
          style: TextStyle(color: Color(0xFF7A7E73), fontSize: 10),
        ),
        const SizedBox(height: 20),

        // 1. YES Button (Hero Action)
        GestureDetector(
          onTap: onYes,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(13),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0xFFFF7752),
                  LisanTheme.orange,
                  Color(0xFFBA381E),
                ],
              ),
              border: Border.all(color: const Color(0xFFFFA085), width: 1.2),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x66F05A36),
                  offset: Offset(0, 4),
                  blurRadius: 10,
                ),
                BoxShadow(
                  color: Color(0x38000000),
                  offset: Offset(0, 2),
                  blurRadius: 4,
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withValues(alpha: 0.22),
                  ),
                  child: const Center(
                    child: Icon(Icons.language, color: Colors.white, size: 20),
                  ),
                ),
                const SizedBox(width: 14),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'YES',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 17,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 1.0,
                        ),
                      ),
                      Text(
                        'I speak English · Auto: EN ⇄ Ethio',
                        style: TextStyle(
                          color: Color(0xFFFFEAE3),
                          fontSize: 10.5,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(
                  Icons.arrow_forward_ios,
                  color: Colors.white,
                  size: 14,
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),

        // 2. ቀጥል Button (Intra-Ethiopian Only / Normal Part)
        GestureDetector(
          onTap: onQetil,
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: const Color(0xFF1B1E1A),
              borderRadius: BorderRadius.circular(13),
              border: Border.all(color: const Color(0xFF454B3E), width: 1.2),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x38000000),
                  offset: Offset(0, 3),
                  blurRadius: 6,
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  width: 36,
                  height: 36,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: LisanTheme.acid.withValues(alpha: 0.15),
                    border: Border.all(
                      color: LisanTheme.acid.withValues(alpha: 0.45),
                    ),
                  ),
                  child: const Center(
                    child: Text(
                      'ቀ',
                      style: TextStyle(
                        color: LisanTheme.acid,
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 14),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'ቀጥል',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 17,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.8,
                        ),
                      ),
                      Text(
                        'Ethiopian Only · የአገር ውስጥ ቋንቋዎች',
                        style: TextStyle(
                          color: Color(0xFF9EA396),
                          fontSize: 10.5,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.check, color: LisanTheme.acid, size: 18),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPartnerSelectionStep({
    required VoidCallback onBack,
    required ValueChanged<AppLanguage> onSelectPartner,
  }) {
    final ethiopianLangs = kLanguages.where((l) => l.code != 'EN').toList();

    return Column(
      key: const ValueKey('step_partner'),
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            GestureDetector(
              onTap: onBack,
              child: Container(
                width: 26,
                height: 26,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: const Color(0xFF1A1D1A),
                  border: Border.all(color: const Color(0xFF383D33)),
                ),
                child: const Center(
                  child: Icon(
                    Icons.arrow_back,
                    size: 14,
                    color: Color(0xFFC3C8BB),
                  ),
                ),
              ),
            ),
            const SizedBox(width: 8),
            const Text(
              'SELECT CONVERSATION PARTNER',
              style: TextStyle(
                color: Color(0xFF888B82),
                fontSize: 8,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.1,
              ),
            ),
          ],
        ),
        const SizedBox(height: 14),
        const Text(
          'Who are you speaking with?',
          style: TextStyle(
            fontFamily: 'serif',
            fontSize: 23,
            color: Colors.white,
            height: 1.15,
            letterSpacing: -0.5,
          ),
        ),
        const SizedBox(height: 3),
        const Text(
          'የአጋርዎን ቋንቋ ይምረጡ',
          style: TextStyle(
            color: LisanTheme.orange,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 14),

        // Grid of 4 Ethiopian Languages
        for (final lang in ethiopianLangs)
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: GestureDetector(
              onTap: () => onSelectPartner(lang),
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  horizontal: 14,
                  vertical: 10,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xFF1B1E1A),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF3B4134)),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x2E000000),
                      offset: Offset(0, 2),
                      blurRadius: 4,
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: lang.tone.withValues(alpha: 0.2),
                        border: Border.all(
                          color: lang.tone.withValues(alpha: 0.6),
                        ),
                      ),
                      child: Center(
                        child: LanguageSymbolWidget(
                          symbol: lang.symbol,
                          size: 16,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          lang.native,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        Text(
                          '${lang.name} (${lang.code})',
                          style: const TextStyle(
                            color: Color(0xFF888B82),
                            fontSize: 9.5,
                          ),
                        ),
                      ],
                    ),
                    const Spacer(),
                    const Icon(
                      Icons.arrow_forward_ios,
                      color: Color(0xFF888B82),
                      size: 12,
                    ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }

  // -------------------------------------------------------------------------
  // Interaction Handlers (Voice & Text)
  // -------------------------------------------------------------------------
  DateTime? _pressStartTime;
  bool _isRecording = false;
  Future<String?>? _stoppingAudioFuture;

  Future<void> _onDialDown() async {
    if (_isRecording) {
      return;
    }

    if (_view != AppView.ready && _view != AppView.result) {
      return;
    }

    if (_haptics) {
      HapticFeedback.heavyImpact();
    }

    _pressStartTime = DateTime.now();
    _isRecording = true;
    _stoppingAudioFuture = null;

    setState(() {
      _view = AppView.speaking;
    });

    try {
      widget.audioCapture.start().then((path) {
        _recordedFilePath = path;
      }).catchError((e) {
        debugPrint('Audio capture start error: $e');
        _isRecording = false;
        if (mounted) {
          setState(() => _view = AppView.ready);
        }
      });
    } catch (e) {
      debugPrint('Audio capture sync start error: $e');
      _isRecording = false;
      if (mounted) {
        setState(() => _view = AppView.ready);
      }
    }
  }

  Future<void> _onDialUp() async {
    if (!_isRecording || _pressStartTime == null) return;

    final elapsed = DateTime.now().difference(_pressStartTime!);
    _isRecording = false;
    _pressStartTime = null;

    if (elapsed < widget.minHoldDuration) {
      // User tapped or released too quickly: cancel recording and inform user to hold
      try {
        widget.audioCapture.stop();
      } catch (_) {}
      if (mounted) {
        setState(() => _view = AppView.ready);
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Row(
              children: [
                Icon(Icons.touch_app_outlined, color: LisanTheme.orange, size: 16),
                SizedBox(width: 8),
                Text(
                  'Hold to speak · release to translate',
                  style: TextStyle(
                    color: Color(0xFFE5E8D9),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
            duration: const Duration(milliseconds: 1800),
            behavior: SnackBarBehavior.floating,
            backgroundColor: const Color(0xFF252924),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: const BorderSide(color: Color(0xFF383C35)),
            ),
          ),
        );
      }
      return;
    }

    // User held button while speaking (push-to-talk): stop & translate!
    if (_haptics) {
      HapticFeedback.mediumImpact();
    }

    // Launch audio stopping in background concurrently without blocking UI
    final stopFuture = widget.audioCapture.stop();
    _stoppingAudioFuture = stopFuture;
    stopFuture.then((path) {
      if (path != null && path.isNotEmpty) {
        _recordedFilePath = path;
      }
    }).catchError((e) {
      debugPrint('Audio capture stop background error: $e');
    });

    if (_conversationMode) {
      final source = _conversationTurn.isEven
          ? _firstLanguage
          : _secondLanguage;
      final target = _conversationTurn.isEven
          ? _secondLanguage
          : _firstLanguage;
      setState(() {
        _language = source;
        _targetLanguage = target;
        _conversationTurn++;
        _view = AppView.loading;
      });
      await _executeTranslation(source: null, target: target);
    } else {
      // INSTANT ZERO-LATENCY POPUP:
      // Instantly transition dial out of speaking state and open "Translate into" sheet!
      setState(() {
        _view = AppView.ready;
      });
      _showTranslateToPrompt();
    }
  }

  Future<void> _beginSpeaking() => _onDialDown();
  Future<void> _finishSpeaking() => _onDialUp();

  Future<void> _chooseLanguage(AppLanguage chosen) async {
    final preferred = kLanguages.firstWhere(
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
    AppLanguage? source,
    required AppLanguage target,
  }) async {
    setState(() {
      _view = AppView.loading;
    });

    // Await background audio recording finalization if it was still completing
    String? audioPath = _recordedFilePath;
    if (_stoppingAudioFuture != null) {
      try {
        final path = await _stoppingAudioFuture;
        if (path != null && path.isNotEmpty) {
          audioPath = path;
        }
      } catch (e) {
        debugPrint('Error awaiting audio stop: $e');
      }
      _stoppingAudioFuture = null;
    }
    _recordedFilePath = null;

    try {
      if (audioPath == null || audioPath.isEmpty) {
        if (mounted) {
          setState(() {
            _sourceText = 'No audio recorded';
            _outputText =
                'ድምፅ አልተቀረጸም - እባክዎ ማይክራፎኑን ነክተው ይናገሩ (Please tap mic and speak clearly)';
            _view = AppView.result;
          });
        }
        return;
      }

      // 1. Offline STT: transcribe audio to text with safety timeout and cleanup
      String transcribedText = '';
      try {
        transcribedText = await _offlineStt
            .transcribe(audioPath)
            .timeout(const Duration(seconds: 30));
      } catch (sttError) {
        debugPrint('[Offline STT Error/Timeout] $sttError');
        if (mounted) {
          setState(() {
            _sourceText = 'Speech recognition error';
            _outputText =
                'ድምፅ መለየት አልተቻለም (Could not process audio: $sttError)';
            _view = AppView.result;
          });
        }
        return;
      } finally {
        // Clean up temporary recorded file
        try {
          final f = File(audioPath);
          if (await f.exists()) await f.delete();
        } catch (_) {}
      }
      debugPrint('[Offline STT] Raw: "$transcribedText"');

      if (transcribedText.trim().isEmpty) {
        if (mounted) {
          setState(() {
            _sourceText = 'No speech detected';
            _outputText =
                'ድምፅ አልተሰማም - እባክዎ ቀርበው ይናገሩ (No speech heard. Speak closer to the phone mic)';
            _view = AppView.result;
          });
        }
        return;
      }

      // -----------------------------------------------------------------------
      // Automatic Spoken Language Recognition (LID) & Speaker's Chosen Target
      // -----------------------------------------------------------------------
      AppLanguage effectiveSource;
      AppLanguage effectiveTarget;

      if (_smartDetect || source == null) {
        final detectedKey = OfflineTranslationMemory.detectLanguage(
          transcribedText,
          defaultLang: (source ?? _language).backendKey,
        );
        debugPrint('[Offline LID] Recognized spoken language: $detectedKey for "$transcribedText"');
        effectiveSource = kLanguages.firstWhere(
          (l) => l.backendKey == detectedKey,
          orElse: () => source ?? _language,
        );

        // Respect the target language chosen by the speaker
        if (effectiveSource.backendKey == target.backendKey) {
          // If speaker chose the same language that was spoken, route to counterpart
          effectiveTarget = (effectiveSource.backendKey == _language.backendKey)
              ? _targetLanguage
              : _language;
          if (effectiveTarget.backendKey == effectiveSource.backendKey) {
            effectiveTarget = (effectiveSource.backendKey == 'eng')
                ? kLanguages[0]
                : kLanguages[4];
          }
        } else {
          effectiveTarget = target;
        }
      } else {
        effectiveSource = source;
        effectiveTarget = target;
      }

      // Clean speech recognition artifacts & acoustic degradation across all 5 languages
      transcribedText = OfflineTranslationMemory.cleanSpokenTranscription(
        transcribedText,
        effectiveSource.backendKey,
      );
      debugPrint('[Offline STT] Cleaned: "$transcribedText" (${effectiveSource.code} -> ${effectiveTarget.code})');

      // 2. Offline NMT: translate
      final translatedText = await _offlineNmt
          .translate(
            transcribedText,
            sourceLang: effectiveSource.backendKey,
            targetLang: effectiveTarget.backendKey,
          )
          .timeout(const Duration(seconds: 30));
      debugPrint('[Offline NMT] "$translatedText"');

      if (mounted) {
        setState(() {
          _language = effectiveSource;
          _targetLanguage = effectiveTarget;
          _sourceText = transcribedText.trim();
          _outputText = translatedText.trim();
          _view = AppView.result;
        });

        if (_autoPlay && translatedText.trim().isNotEmpty) {
          _playAudio();
        }
      }
    } catch (e) {
      debugPrint('Offline translation error: $e');
      if (mounted) {
        setState(() {
          _sourceText = 'Translation error';
          _outputText = 'Offline error: $e';
          _view = AppView.result;
        });
      }
    }
  }


  Future<void> _executeTextTranslation({
    required String text,
    required AppLanguage source,
    required AppLanguage target,
  }) async {
    if (text.trim().isEmpty) return;

    AppLanguage effectiveSrc = source;
    AppLanguage effectiveTgt = target;

    if (_smartDetect) {
      final detectedKey = OfflineTranslationMemory.detectLanguage(
        text,
        defaultLang: source.backendKey,
      );
      effectiveSrc = kLanguages.firstWhere(
        (l) => l.backendKey == detectedKey,
        orElse: () => source,
      );
      if (effectiveSrc.backendKey == effectiveTgt.backendKey) {
        effectiveTgt = (effectiveSrc.backendKey == 'eng')
            ? kLanguages[0]
            : kLanguages[4];
      }
    }

    setState(() {
      _language = effectiveSrc;
      _targetLanguage = effectiveTgt;
      _view = AppView.result;
    });

    try {
      final translatedText = await _offlineNmt.translate(
        text.trim(),
        sourceLang: effectiveSrc.backendKey,
        targetLang: effectiveTgt.backendKey,
      );
      // NMT session kept warm in memory for rapid subsequent text translations.
      // Automatically freed if user switches to voice mode in _onDialDown().

      if (mounted) {
        setState(() {
          _sourceText = text.trim();
          _outputText = translatedText.trim();
        });

        if (_autoPlay && translatedText.trim().isNotEmpty) {
          _playAudio();
        }
      }
    } catch (e) {
      debugPrint('Offline text translation error: $e');
      if (mounted) {
        setState(() {
          _sourceText = text;
          _outputText = 'Offline error: $e';
        });
      }
    }
  }

  Future<void> _playAudio() async {
    final text = _outputText.trim();
    if (text.isEmpty ||
        text.startsWith('ድምፅ አልተሰማም') ||
        text.startsWith('ድምፅ አልተቀረጸም') ||
        text.startsWith('Offline error') ||
        text.startsWith('Error:')) {
      return;
    }

    setState(() => _playing = true);
    _playbackTimer?.cancel();

    try {
      final langKey = _targetLanguage.backendKey;
      final cacheKey = computeTtsCacheKey(langKey, text);
      final cacheCandidates = [
        '/sdcard/lisan_models/tts_cache/$cacheKey.wav',
        '/storage/emulated/0/lisan_models/tts_cache/$cacheKey.wav',
      ];

      File? matchedFile;
      for (final p in cacheCandidates) {
        final f = File(p);
        if (f.existsSync() && f.lengthSync() > 500) {
          matchedFile = f;
          break;
        }
      }

      if (matchedFile != null) {
        debugPrint('[TTS] Playing neural cached MMS-TTS voice: ${matchedFile.path}');
        await _audioPlayer.stop();
        await _audioPlayer.play(DeviceFileSource(matchedFile.path));
        return;
      }

      debugPrint('[TTS] Cache miss for "$text" ($langKey). Falling back to NativeTts');
      final spoke = await NativeTts.speak(text, langKey);
      if (!spoke) {
        debugPrint('[TTS] NativeTts could not vocalize text.');
      }

      // Reset playing state after estimated reading time
      final estimatedMs = (text.length * 80).clamp(2000, 8000);
      _playbackTimer = Timer(Duration(milliseconds: estimatedMs), () {
        if (mounted) setState(() => _playing = false);
      });
    } catch (e) {
      debugPrint('TTS play error: $e');
      if (mounted) setState(() => _playing = false);
    }
  }

  void _reset() {
    _audioPlayer.stop();
    NativeTts.stop();
    _playbackTimer?.cancel();
    setState(() {
      _view = AppView.ready;
      _playing = false;
    });
  }


  void _showTextInputDialog() {
    final textController = TextEditingController();
    AppLanguage selectedSrc = _language;
    AppLanguage selectedTgt = _targetLanguage;
    if (selectedSrc.code == selectedTgt.code) {
      selectedTgt = selectedSrc.code == 'EN' ? kLanguages[0] : kLanguages[4];
    }

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: LisanTheme.well,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (context, setSheetState) {
            return Padding(
              padding: EdgeInsets.only(
                left: 20,
                right: 20,
                top: 20,
                bottom: MediaQuery.of(context).viewInsets.bottom + 20,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'TEXT TRANSLATION',
                        style: TextStyle(
                          color: LisanTheme.acid,
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 1.5,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, color: Color(0xFFC3C8BB)),
                        onPressed: () => Navigator.pop(ctx),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: DropdownButtonFormField<AppLanguage>(
                          key: ValueKey('src_${selectedSrc.code}'),
                          initialValue: selectedSrc,
                          isExpanded: true,
                          dropdownColor: LisanTheme.wellDeep,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                          ),
                          decoration: InputDecoration(
                            labelText: 'From',
                            labelStyle: const TextStyle(
                              color: LisanTheme.muted,
                              fontSize: 11,
                            ),
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 8,
                            ),
                            filled: true,
                            fillColor: const Color(0xFF1E221E),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          items: kLanguages.map((l) {
                            return DropdownMenuItem(
                              value: l,
                              child: Text(
                                '${l.native} (${l.code})',
                                overflow: TextOverflow.ellipsis,
                              ),
                            );
                          }).toList(),
                          onChanged: (val) {
                            if (val != null) {
                              setSheetState(() {
                                selectedSrc = val;
                                if (selectedTgt.code == selectedSrc.code) {
                                  selectedTgt = selectedSrc.code == 'EN'
                                      ? kLanguages[0]
                                      : kLanguages[4];
                                }
                              });
                            }
                          },
                        ),
                      ),
                      const SizedBox(width: 6),
                      GestureDetector(
                        onTap: () {
                          setSheetState(() {
                            final tmp = selectedSrc;
                            selectedSrc = selectedTgt;
                            selectedTgt = tmp;
                          });
                        },
                        child: Container(
                          padding: const EdgeInsets.all(7),
                          decoration: BoxDecoration(
                            color: const Color(0xFF242823),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: const Color(0xFF454B3E)),
                          ),
                          child: const Icon(
                            Icons.swap_horiz,
                            color: LisanTheme.acid,
                            size: 18,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: DropdownButtonFormField<AppLanguage>(
                          key: ValueKey('tgt_${selectedTgt.code}'),
                          initialValue: selectedTgt,
                          isExpanded: true,
                          dropdownColor: LisanTheme.wellDeep,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                          ),
                          decoration: InputDecoration(
                            labelText: 'To',
                            labelStyle: const TextStyle(
                              color: LisanTheme.muted,
                              fontSize: 11,
                            ),
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 10,
                              vertical: 8,
                            ),
                            filled: true,
                            fillColor: const Color(0xFF1E221E),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                          items: kLanguages.map((l) {
                            return DropdownMenuItem(
                              value: l,
                              child: Text(
                                '${l.native} (${l.code})',
                                overflow: TextOverflow.ellipsis,
                              ),
                            );
                          }).toList(),
                          onChanged: (val) {
                            if (val != null) {
                              setSheetState(() {
                                selectedTgt = val;
                                if (selectedSrc.code == selectedTgt.code) {
                                  selectedSrc = selectedTgt.code == 'EN'
                                      ? kLanguages[0]
                                      : kLanguages[4];
                                }
                              });
                            }
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: textController,
                    autofocus: true,
                    maxLines: 3,
                    style: const TextStyle(color: Colors.white, fontSize: 15),
                    decoration: InputDecoration(
                      hintText: 'Enter text to translate...',
                      hintStyle: TextStyle(
                        color: Colors.white.withValues(alpha: 0.35),
                      ),
                      filled: true,
                      fillColor: const Color(0xFF181B18),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(color: Color(0xFF353932)),
                      ),
                      focusedBorder: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(10),
                        borderSide: const BorderSide(color: LisanTheme.orange),
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: LisanTheme.orange,
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                      ),
                      onPressed: () {
                        final input = textController.text.trim();
                        if (input.isNotEmpty) {
                          Navigator.pop(ctx);
                          _executeTextTranslation(
                            text: input,
                            source: selectedSrc,
                            target: selectedTgt,
                          );
                        }
                      },
                      child: const Text(
                        'TRANSLATE',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          letterSpacing: 1.2,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
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
                            color: const Color(
                              0xFF363731,
                            ).withValues(alpha: 0.28),
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
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: const BoxDecoration(
        border: Border(bottom: BorderSide(color: Color(0x3831322D))),
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
                      BoxShadow(color: Color(0xFFFFF9E8), offset: Offset(0, 2)),
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

          Row(
            children: [
              // Type Text button
              GestureDetector(
                onTap: _showTextInputDialog,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(7),
                    border: Border.all(color: const Color(0xFF9C9587)),
                    gradient: const LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Color(0xFFEEE7D8), Color(0xFFC9C1B1)],
                    ),
                    boxShadow: const [
                      BoxShadow(color: Color(0xFF9F988A), offset: Offset(0, 2)),
                      BoxShadow(
                        color: Color(0x24353028),
                        offset: Offset(0, 4),
                        blurRadius: 6,
                      ),
                    ],
                  ),
                  child: const Row(
                    children: [
                      Icon(Icons.edit_note, size: 14, color: Color(0xFF474942)),
                      SizedBox(width: 4),
                      Text(
                        'Type text',
                        style: TextStyle(
                          color: Color(0xFF474942),
                          fontSize: 9.5,
                          fontWeight: FontWeight.w700,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 6),

              // Advanced settings button
              GestureDetector(
                onTap: () {
                  setState(() {
                    _view = AppView.settings;
                  });
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(7),
                    border: Border.all(color: const Color(0xFF9C9587)),
                    gradient: const LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [Color(0xFFEEE7D8), Color(0xFFC9C1B1)],
                    ),
                    boxShadow: const [
                      BoxShadow(color: Color(0xFF9F988A), offset: Offset(0, 2)),
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
                        'Settings',
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
                        size: 12,
                        color: Color(0xFF474942),
                      ),
                    ],
                  ),
                ),
              ),
            ],
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
      case AppView.loading:
        return _buildLoadingView();
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
              Container(width: 19, height: 2, color: LisanTheme.orange),
              const SizedBox(width: 9),
              Text(
                isSpeaking
                    ? 'LISTENING NOW'
                    : (_offlineReady
                        ? 'OFFLINE · ON-DEVICE AI'
                        : 'INITIALIZING OFFLINE AI…'),
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
                fontSize: 44,
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
                  fontSize: 46,
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
          const SizedBox(height: 10),

          // Hero Copy
          Text(
            isSpeaking
                ? 'Keep holding while you speak · Release to translate'
                : 'Instant translation across the languages of Ethiopia and the Horn.',
            style: const TextStyle(
              color: LisanTheme.muted,
              fontSize: 12,
              height: 1.4,
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
                  BoxShadow(color: Color(0xFFF9F2E3), offset: Offset(0, 1)),
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
                        BoxShadow(color: _firstLanguage.tone, blurRadius: 4),
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
                        BoxShadow(color: _secondLanguage.tone, blurRadius: 4),
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
            child: RepaintBoundary(
              child: _OrbStage(
                isSpeaking: isSpeaking,
                onDialDown: _onDialDown,
                onDialUp: _onDialUp,
              ),
            ),
          ),
          const SizedBox(height: 14),
          Center(
            child: Text(
              isSpeaking
                  ? 'RECORDING · RELEASE TO TRANSLATE'
                  : 'HOLD TO SPEAK',
              style: TextStyle(
                color: isSpeaking ? LisanTheme.orange : const Color(0xFF8A887E),
                fontSize: 9.5,
                fontWeight: FontWeight.w700,
                letterSpacing: 1.5,
              ),
            ),
          ),
          const SizedBox(height: 18),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------------
  // Post-Recording "Translate To" Aesthetic Prompt (Referenced from Settings Section 01)
  // -------------------------------------------------------------------------
  Future<void> _showTranslateToPrompt() async {
    final chosen = await showModalBottomSheet<AppLanguage>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      barrierColor: const Color(0xB80E100D),
      builder: (sheetCtx) {
        return Container(
          decoration: const BoxDecoration(
            color: LisanTheme.paperLight,
            borderRadius: BorderRadius.vertical(top: Radius.circular(22)),
            border: Border(
              top: BorderSide(color: Color(0xFF8F887B), width: 2),
              left: BorderSide(color: Color(0xFF8F887B), width: 2),
              right: BorderSide(color: Color(0xFF8F887B), width: 2),
            ),
            boxShadow: [
              BoxShadow(
                color: Color(0x66000000),
                offset: Offset(0, -6),
                blurRadius: 20,
              ),
            ],
          ),
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 26),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Micro-kicker header
              Row(
                children: [
                  Container(width: 19, height: 2.5, color: LisanTheme.orange),
                  const SizedBox(width: 8),
                  const Text(
                    'VOICE CAPTURED · SELECT TARGET',
                    style: TextStyle(
                      color: Color(0xFF62645C),
                      fontSize: 9.5,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.5,
                    ),
                  ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () => Navigator.of(sheetCtx).pop(null),
                    child: Container(
                      width: 26,
                      height: 26,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: const Color(0xFFDDD5C6),
                        border: Border.all(color: const Color(0xFF9E9789)),
                      ),
                      child: const Center(
                        child: Icon(
                          Icons.close,
                          size: 14,
                          color: Color(0xFF4A4B44),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),

              // Title
              const Text(
                'Translate into',
                style: TextStyle(
                  fontFamily: 'serif',
                  fontSize: 30,
                  color: LisanTheme.ink,
                  height: 1.0,
                  letterSpacing: -0.8,
                ),
              ),
              const SizedBox(height: 2),
              const Text(
                'መተርጎሚያ ቋንቋ ይምረጡ',
                style: TextStyle(
                  color: LisanTheme.orange,
                  fontSize: 13.5,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(height: 16),

              // Aesthetic Select Box (matching Settings Section 01: TRANSLATION)
              _buildSettingsStyleTranslateBox(sheetCtx),
            ],
          ),
        );
      },
    );

    if (!mounted) return;

    if (chosen != null) {
      setState(() {
        _targetLanguage = chosen;
        _view = AppView.loading;
      });
      // Yield to allow the loading frame to paint cleanly before running translation
      await WidgetsBinding.instance.endOfFrame;
      if (mounted) {
        await _executeTranslation(source: null, target: chosen);
      }
    } else {
      _cleanupPendingRecording();
      if (mounted && _view != AppView.result) {
        setState(() => _view = AppView.ready);
      }
    }
  }

  void _cleanupPendingRecording() {
    final pending = _stoppingAudioFuture;
    _stoppingAudioFuture = null;
    final path = _recordedFilePath;
    _recordedFilePath = null;

    if (pending != null) {
      pending.then((stopped) {
        if (stopped != null && stopped.isNotEmpty) {
          try {
            final f = File(stopped);
            if (f.existsSync()) f.deleteSync();
          } catch (_) {}
        }
      });
    } else if (path != null && path.isNotEmpty) {
      try {
        final f = File(path);
        if (f.existsSync()) f.deleteSync();
      } catch (_) {}
    }
  }

  Widget _buildSettingsStyleTranslateBox(BuildContext sheetCtx) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFC8C0B1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF8F887B)),
        boxShadow: const [
          BoxShadow(color: Color(0xFFFFF8E9), offset: Offset(0, 1)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'OUTPUT LANGUAGE',
                style: TextStyle(
                  color: Color(0xFF30322D),
                  fontSize: 10,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.0,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: LisanTheme.acid.withValues(alpha: 0.18),
                  borderRadius: BorderRadius.circular(4),
                  border: Border.all(color: const Color(0xFF6B7A24)),
                ),
                child: const Text(
                  'INSTANT SYNTHESIS',
                  style: TextStyle(
                    color: Color(0xFF344012),
                    fontSize: 7.5,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 3),
          const Text(
            'Spoken language is auto-detected · Tap target language to translate',
            style: TextStyle(color: Color(0xFF74746C), fontSize: 8.8),
          ),
          const SizedBox(height: 12),

          // Primary Row: Amharic & English
          Row(
            children: [
              Expanded(
                child: _buildSelectBoxLanguageButton(sheetCtx, kLanguages[0]),
              ), // Amharic
              const SizedBox(width: 8),
              Expanded(
                child: _buildSelectBoxLanguageButton(sheetCtx, kLanguages[4]),
              ), // English
            ],
          ),
          const SizedBox(height: 8),

          // Secondary Row: Afaan Oromoo & Tigrinya
          Row(
            children: [
              Expanded(
                child: _buildSelectBoxLanguageButton(sheetCtx, kLanguages[1]),
              ), // Oromo
              const SizedBox(width: 8),
              Expanded(
                child: _buildSelectBoxLanguageButton(sheetCtx, kLanguages[2]),
              ), // Tigrinya
            ],
          ),
          const SizedBox(height: 8),

          // Third Row: Somali
          Row(
            children: [
              Expanded(
                child: _buildSelectBoxLanguageButton(sheetCtx, kLanguages[3]),
              ), // Somali
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSelectBoxLanguageButton(
    BuildContext sheetCtx,
    AppLanguage lang,
  ) {
    final isSelected = _targetLanguage.code == lang.code;
    return GestureDetector(
      onTap: () {
        if (_haptics) {
          HapticFeedback.lightImpact();
        }
        Navigator.of(sheetCtx).pop(lang);
      },
      child: Container(
        height: 44,
        padding: const EdgeInsets.symmetric(horizontal: 10),
        decoration: BoxDecoration(
          color: isSelected ? LisanTheme.well : const Color(0xFFE8E1D3),
          borderRadius: BorderRadius.circular(7),
          border: Border.all(
            color: isSelected
                ? const Color(0xFF171916)
                : const Color(0xFF8D8679),
            width: 1.2,
          ),
          boxShadow: [
            if (!isSelected)
              const BoxShadow(color: Color(0xFF918A7D), offset: Offset(0, 2)),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isSelected
                    ? lang.tone.withValues(alpha: 0.35)
                    : lang.tone.withValues(alpha: 0.18),
                border: Border.all(
                  color: isSelected ? lang.tone : const Color(0xFF8B8478),
                ),
              ),
              child: Center(
                child: LanguageSymbolWidget(
                  symbol: lang.symbol,
                  size: 12,
                  color: isSelected ? Colors.white : const Color(0xFF3E4039),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Flexible(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    lang.native,
                    style: TextStyle(
                      color: isSelected
                          ? LisanTheme.acid
                          : const Color(0xFF30322D),
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                  Text(
                    '${lang.name} (${lang.code})',
                    style: TextStyle(
                      color: isSelected
                          ? const Color(0xFF9FA596)
                          : const Color(0xFF74746C),
                      fontSize: 8,
                      fontWeight: FontWeight.w500,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            if (isSelected) ...[
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
                        Container(
                          width: 19,
                          height: 2,
                          color: LisanTheme.orange,
                        ),
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
              _buildIconButton(icon: LisanIconType.close, onTap: _reset),
            ],
          ),
          const SizedBox(height: 12),
          const Text(
            'Choose by color or symbol',
            style: TextStyle(color: LisanTheme.muted, fontSize: 11),
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
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.32),
                    ),
                    color: const Color(0x381C1D19),
                    boxShadow: const [
                      BoxShadow(color: Color(0x33FFFFFF), offset: Offset(0, 1)),
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
                  BoxShadow(color: Color(0x33FFFFFF), offset: Offset(0, 1)),
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
  // 2.5 Minimalist Aesthetic Loading Screen (Warm Light Theme)
  // -------------------------------------------------------------------------
  Widget _buildLoadingView() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 28, 22, 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Eyebrow
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(width: 19, height: 2, color: LisanTheme.orange),
                  const SizedBox(width: 9),
                  const Text(
                    'TRANSLATING NOW',
                    style: TextStyle(
                      color: Color(0xFF62645C),
                      fontSize: 9.5,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.8,
                    ),
                  ),
                ],
              ),
              _buildIconButton(icon: LisanIconType.close, onTap: _reset),
            ],
          ),
          const SizedBox(height: 14),

          // Hero Display Title (Serif)
          Text.rich(
            TextSpan(
              style: const TextStyle(
                fontFamily: 'serif',
                fontSize: 44,
                color: LisanTheme.ink,
                height: 0.95,
                letterSpacing: -1.5,
              ),
              children: [
                const TextSpan(text: 'Translating…\n'),
                TextSpan(
                  text: '${_targetLanguage.native} (${_targetLanguage.name})',
                  style: TextStyle(
                    color: _targetLanguage.tone,
                    fontStyle: FontStyle.italic,
                    fontSize: 26,
                    letterSpacing: -0.5,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),

          // Subtitle
          const Text(
            'Synthesizing speech with natural inflection and clarity.',
            style: TextStyle(
              color: LisanTheme.muted,
              fontSize: 12,
              height: 1.4,
            ),
          ),

          const Spacer(),

          // Sculptural Minimalist Centerpiece
          Center(
            child: RepaintBoundary(
              child: LisanAestheticOrb(targetLanguage: _targetLanguage),
            ),
          ),

          const Spacer(),

          // Cancel / Abort Button
          GestureDetector(
            onTap: _reset,
            child: Container(
              width: double.infinity,
              height: 50,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(9),
                border: Border.all(color: const Color(0xFF9E9687)),
                gradient: const LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0xFFEEE7D8), Color(0xFFC9C1B1)],
                ),
                boxShadow: const [
                  BoxShadow(color: Color(0xFF9F988A), offset: Offset(0, 2)),
                  BoxShadow(
                    color: Color(0x24353028),
                    offset: Offset(0, 4),
                    blurRadius: 6,
                  ),
                ],
              ),
              child: const Center(
                child: Text(
                  'CANCEL',
                  style: TextStyle(
                    color: Color(0xFF474942),
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 1.6,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  // -------------------------------------------------------------------------
  // 3. Aesthetic Light-Themed Translation Card Result View
  // -------------------------------------------------------------------------
  Widget _buildResultView() {
    return SingleChildScrollView(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(22, 16, 22, 28),
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
                        Container(
                          width: 19,
                          height: 2,
                          color: LisanTheme.orange,
                        ),
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
              _buildIconButton(icon: LisanIconType.close, onTap: _reset),
            ],
          ),
          const SizedBox(height: 18),

          // Main Card - Light Theme Warm Paper Chassis
          Container(
            width: double.infinity,
            decoration: BoxDecoration(
              color: LisanTheme.paperLight,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: const Color(0xFFD4CDC0), width: 1.2),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x1A28251E),
                  offset: Offset(0, 6),
                  blurRadius: 16,
                ),
                BoxShadow(
                  color: Color(0xFFFFFDF8),
                  offset: Offset(0, 1),
                  blurRadius: 0,
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Top Section: Source Speech
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 20, 20, 18),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          _buildMiniSwatch(_language),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '${_language.name.toUpperCase()} (${_language.native})',
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                color: Color(0xFF666A60),
                                fontSize: 9.5,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.8,
                              ),
                            ),
                          ),
                          const SizedBox(width: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 3.5,
                            ),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(5),
                              border: Border.all(
                                color: const Color(0xFFBFB7A8),
                              ),
                              color: const Color(0xFFE4DECF),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Container(
                                  width: 5,
                                  height: 5,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: _language.tone,
                                  ),
                                ),
                                const SizedBox(width: 4),
                                const Text(
                                  'AUTO-RECOGNISED',
                                  style: TextStyle(
                                    color: Color(0xFF62665C),
                                    fontSize: 7.5,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.6,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Text(
                        _sourceText.isEmpty
                            ? 'No speech transcribed yet'
                            : _sourceText,
                        style: TextStyle(
                          color: _sourceText.isEmpty
                              ? const Color(0xFF8A887E)
                              : LisanTheme.ink,
                          fontSize: 16,
                          height: 1.5,
                          fontWeight: FontWeight.w400,
                        ),
                      ),
                    ],
                  ),
                ),

                // Divider Line
                Container(
                  width: double.infinity,
                  height: 1,
                  color: const Color(0xFFDCD5C6),
                ),

                // Bottom Section: Output Translation
                Padding(
                  padding: const EdgeInsets.fromLTRB(20, 18, 20, 20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          _buildMiniSwatch(_targetLanguage),
                          const SizedBox(width: 10),
                          Text(
                            '${_targetLanguage.name.toUpperCase()} (${_targetLanguage.native})',
                            style: TextStyle(
                              color: _targetLanguage.tone,
                              fontSize: 9.5,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.8,
                            ),
                          ),
                          const Spacer(),
                          // Copy button
                          GestureDetector(
                            onTap: () {
                              if (_outputText.isNotEmpty) {
                                Clipboard.setData(
                                  ClipboardData(text: _outputText),
                                );
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: const Text(
                                      'Translation copied to clipboard',
                                      style: TextStyle(fontSize: 12),
                                    ),
                                    duration: const Duration(seconds: 2),
                                    behavior: SnackBarBehavior.floating,
                                    backgroundColor: const Color(0xFF2C2F29),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                  ),
                                );
                              }
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 3.5,
                              ),
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(5),
                                border: Border.all(
                                  color: const Color(0xFFC8C1B2),
                                ),
                                color: const Color(0xFFE8E2D4),
                              ),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    Icons.copy,
                                    size: 11,
                                    color: Color(0xFF5A5C54),
                                  ),
                                  SizedBox(width: 4),
                                  Text(
                                    'COPY',
                                    style: TextStyle(
                                      color: Color(0xFF5A5C54),
                                      fontSize: 7.5,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 0.6,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      Text(
                        _outputText.isEmpty
                            ? 'Tap mic or type text to translate'
                            : _outputText,
                        style: TextStyle(
                          fontFamily: 'serif',
                          color: _outputText.isEmpty
                              ? const Color(0xFF8A887E)
                              : LisanTheme.ink,
                          fontSize: _outputText.isEmpty ? 18 : 28,
                          height: 1.25,
                          letterSpacing: -0.5,
                        ),
                      ),
                      const SizedBox(height: 22),

                      // Audio Playback Bar
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 10,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFE4DDD0),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFFCCC5B6)),
                        ),
                        child: Row(
                          children: [
                            GestureDetector(
                              onTap: () {
                                if (_playing) {
                                  _audioPlayer.stop();
                                  NativeTts.stop();
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
                                  color: LisanTheme.orange,
                                  boxShadow: [
                                    BoxShadow(
                                      color: Color(0x35000000),
                                      offset: Offset(0, 3),
                                      blurRadius: 6,
                                    ),
                                  ],
                                ),
                                child: Center(
                                  child: Icon(
                                    _playing
                                        ? Icons.stop_rounded
                                        : Icons.volume_up_rounded,
                                    size: 20,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: WaveformEqualizer(
                                active: _playing,
                                color: _targetLanguage.tone,
                              ),
                            ),
                            const SizedBox(width: 10),
                            Text(
                              _audioDurationText,
                              style: const TextStyle(
                                color: Color(0xFF6B6E64),
                                fontSize: 9.5,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          // Action Buttons
          if (_conversationMode) ...[
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFFE4DDD0),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: const Color(0xFFCCC5B6)),
              ),
              child: Row(
                children: [
                  Container(
                    width: 9,
                    height: 9,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _targetLanguage.tone,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _targetLanguage.name,
                        style: const TextStyle(
                          color: LisanTheme.ink,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const Text(
                        'Next speaker reply',
                        style: TextStyle(
                          color: LisanTheme.muted,
                          fontSize: 8.5,
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
                          width: 3.5,
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
                            color: Color(0x35000000),
                            offset: Offset(0, 4),
                            blurRadius: 6,
                          ),
                        ],
                      ),
                      child: const Center(
                        child: LisanIcon(
                          LisanIconType.mic,
                          size: 22,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  const SizedBox(
                    width: 44,
                    child: Text(
                      'HOLD TO REPLY',
                      style: TextStyle(
                        color: Color(0xFF62645C),
                        fontSize: 8,
                        fontWeight: FontWeight.w700,
                        height: 1.3,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
          ],
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
          const SizedBox(height: 12),
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
        border: Border.all(color: Color.lerp(lang.tone, Colors.white, 0.45)!),
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
                        Container(
                          width: 19,
                          height: 2,
                          color: LisanTheme.orange,
                        ),
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
              _buildIconButton(icon: LisanIconType.close, onTap: _reset),
            ],
          ),
          const SizedBox(height: 20),

          // Section 00: Speaker Persona
          _buildSettingsGroupHeader('SPEAKER PERSONA', '00'),
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFC8C0B1),
              borderRadius: BorderRadius.circular(11),
              border: Border.all(color: const Color(0xFF8F887B)),
              boxShadow: const [
                BoxShadow(color: Color(0xFFFFF8E9), offset: Offset(0, 1)),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _isEnglishSpeaker
                            ? 'English Speaker (YES)'
                            : 'Ethiopian Only (ቀጥል)',
                        style: const TextStyle(
                          color: Color(0xFF30322D),
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        _isEnglishSpeaker
                            ? 'Auto-routes: English ⇄ ${_targetLanguage.name}'
                            : 'Intra-Ethiopian LID (0% English false override)',
                        style: const TextStyle(
                          color: Color(0xFF74746C),
                          fontSize: 8.5,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: () => _showPersonaSetupDialog(canDismiss: true),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: LisanTheme.well,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: const Color(0xFF1E211D)),
                    ),
                    child: const Text(
                      'Change',
                      style: TextStyle(
                        color: LisanTheme.acid,
                        fontSize: 9.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ],
            ),
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
                BoxShadow(color: Color(0xFFFFF8E9), offset: Offset(0, 1)),
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
                  style: TextStyle(color: Color(0xFF74746C), fontSize: 8.5),
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
                BoxShadow(color: Color(0xFFFFF8E9), offset: Offset(0, 1)),
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
                    style: TextStyle(color: Color(0xFF74746C), fontSize: 8),
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
                        onSelect: (lang) =>
                            setState(() => _firstLanguage = lang),
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
                        onSelect: (lang) =>
                            setState(() => _secondLanguage = lang),
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
                BoxShadow(color: Color(0xFFFFF8E9), offset: Offset(0, 1)),
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
                BoxShadow(color: Color(0xFFFFF8E9), offset: Offset(0, 1)),
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
                  style: TextStyle(color: Color(0xFF666860), fontSize: 7.5),
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
            style: const TextStyle(color: Color(0xFF74746C), fontSize: 8),
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
          style: const TextStyle(color: Color(0xFF64665F), fontSize: 8.5),
        ),
        Row(
          children: [
            for (final lang in kLanguages)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2),
                child: GestureDetector(
                  onTap: lang.code == blocked.code
                      ? null
                      : () => onSelect(lang),
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
      behavior: HitTestBehavior.opaque,
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
            BoxShadow(color: Color(0xFF9E978A), offset: Offset(0, 2)),
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
            BoxShadow(color: Color(0xFF8F301E), offset: Offset(0, 3)),
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
            BoxShadow(color: Color(0xFFEEE7D8), offset: Offset(0, 1)),
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
    required this.onDialDown,
    required this.onDialUp,
  });

  final bool isSpeaking;
  final VoidCallback onDialDown;
  final VoidCallback onDialUp;

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
    return RepaintBoundary(
      child: SizedBox(
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
                              ? LisanTheme.orange.withValues(
                                  alpha: ringOpacity3,
                                )
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
                              ? LisanTheme.orange.withValues(
                                  alpha: ringOpacity2,
                                )
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
                              ? LisanTheme.orange.withValues(
                                  alpha: ringOpacity1,
                                )
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

          // Central 126px Tactile Dial with expanded 170px hit area
          Listener(
            key: const ValueKey('mic_dial_button'),
            behavior: HitTestBehavior.opaque,
            onPointerDown: (_) => widget.onDialDown(),
            onPointerUp: (_) => widget.onDialUp(),
            onPointerCancel: (_) => widget.onDialUp(),
            child: Container(
              width: 170,
              height: 170,
              color: Colors.transparent,
              alignment: Alignment.center,
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
                    const BoxShadow(color: Color(0xFF151713), spreadRadius: 2),
                    const BoxShadow(color: Color(0xFFA9A191), spreadRadius: 8),
                    const BoxShadow(color: Color(0xFFF6EFDF), spreadRadius: 10),
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
                            colors: [Color(0x56FFFFFF), Colors.transparent],
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
          ),
        ],
      ),
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
    0.24,
    0.40,
    0.62,
    0.34,
    0.76,
    0.52,
    0.88,
    0.60,
    0.38,
    0.70,
    0.46,
    0.82,
    0.56,
    0.34,
    0.64,
    0.44,
    0.28,
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
    return RepaintBoundary(
      child: AnimatedBuilder(
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
                  final wave = math.sin(
                    _waveController.value * math.pi * 2 + phase,
                  );
                  heightFactor = (base * (0.45 + wave.abs() * 0.55)).clamp(
                    0.15,
                    1.0,
                  );
                }
                return Container(
                  width: 2.2,
                  height: 32 * heightFactor,
                  margin: const EdgeInsets.symmetric(horizontal: 1.5),
                  decoration: BoxDecoration(
                    color: widget.color.withValues(
                      alpha: widget.active ? 0.95 : 0.45,
                    ),
                    borderRadius: BorderRadius.circular(1.1),
                  ),
                );
              }),
            ),
          );
        },
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Clean, Minimal & Sculptural Acoustic Orb Visualizer (White/Light Theme)
// ---------------------------------------------------------------------------
class LisanAestheticOrb extends StatefulWidget {
  const LisanAestheticOrb({super.key, required this.targetLanguage});

  final AppLanguage targetLanguage;

  @override
  State<LisanAestheticOrb> createState() => _LisanAestheticOrbState();
}

class _LisanAestheticOrbState extends State<LisanAestheticOrb>
    with TickerProviderStateMixin {
  late final AnimationController _pulseController;
  late final AnimationController _orbitController;
  late final AnimationController _waveController;

  @override
  void initState() {
    super.initState();
    // Gentle breathing pulse (1.6s)
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1600),
    )..repeat(reverse: true);

    // Smooth continuous orbital rotation (4.0s)
    _orbitController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 4000),
    )..repeat();

    // Harmonic soundwave modulation (900ms)
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _orbitController.dispose();
    _waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: AnimatedBuilder(
        animation: Listenable.merge([
        _pulseController,
        _orbitController,
        _waveController,
      ]),
      builder: (context, _) {
        final pulse = _pulseController.value;
        final orbit = _orbitController.value * 2 * math.pi;
        final tone = widget.targetLanguage.tone;

        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Centerpiece: Breathing Rings & Tactile Language Orb
            SizedBox(
              width: 250,
              height: 250,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  // Outer Acoustic Wave Ring 3 (240px)
                  Transform.scale(
                    scale: 0.90 + pulse * 0.18,
                    child: Container(
                      width: 236,
                      height: 236,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: tone.withValues(
                            alpha: (0.16 * (1.0 - pulse * 0.4)).clamp(
                              0.04,
                              0.2,
                            ),
                          ),
                          width: 1.2,
                        ),
                      ),
                    ),
                  ),

                  // Outer Acoustic Wave Ring 2 (198px)
                  Transform.scale(
                    scale: 0.94 + pulse * 0.14,
                    child: Container(
                      width: 196,
                      height: 196,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: tone.withValues(
                            alpha: (0.24 * (1.0 - pulse * 0.3)).clamp(
                              0.06,
                              0.28,
                            ),
                          ),
                          width: 1.2,
                        ),
                      ),
                    ),
                  ),

                  // Outer Acoustic Wave Ring 1 (156px)
                  Transform.scale(
                    scale: 0.97 + pulse * 0.08,
                    child: Container(
                      width: 156,
                      height: 156,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: tone.withValues(
                            alpha: (0.35 * (1.0 - pulse * 0.25)).clamp(
                              0.1,
                              0.4,
                            ),
                          ),
                          width: 1.5,
                        ),
                      ),
                    ),
                  ),

                  // Rotating Orbital Satellite Ring
                  Transform.rotate(
                    angle: orbit,
                    child: CustomPaint(
                      size: const Size(140, 140),
                      painter: OrbitalShimmerPainter(tone: tone),
                    ),
                  ),

                  // Tactile Sculptural Center Orb (diameter: 104px)
                  Container(
                    width: 104,
                    height: 104,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: const Color(0xFF30332D),
                        width: 5,
                      ),
                      gradient: RadialGradient(
                        center: const Alignment(-0.35, -0.4),
                        radius: 0.85,
                        colors: [
                          Color.lerp(tone, Colors.white, 0.42)!,
                          tone,
                          Color.lerp(tone, const Color(0xFF1E211A), 0.35)!,
                        ],
                        stops: const [0.0, 0.55, 1.0],
                      ),
                      boxShadow: [
                        // Warm chassis recess bevel
                        const BoxShadow(
                          color: Color(0xFFECE5D5),
                          offset: Offset(0, 0),
                          spreadRadius: 3,
                        ),
                        // Soft tone glow
                        BoxShadow(
                          color: tone.withValues(alpha: 0.38),
                          offset: const Offset(0, 8),
                          blurRadius: 22,
                          spreadRadius: 2,
                        ),
                        // Ground drop shadow
                        const BoxShadow(
                          color: Color(0x38342C23),
                          offset: Offset(0, 8),
                          blurRadius: 10,
                        ),
                      ],
                    ),
                    child: Center(
                      child: LanguageSymbolWidget(
                        symbol: widget.targetLanguage.symbol,
                        size: 42,
                        color: const Color(0xFFFFF8E9),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Delicate Minimal Harmonic Waveform
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: List.generate(9, (i) {
                const baseFactors = [
                  0.35,
                  0.6,
                  0.9,
                  0.7,
                  1.0,
                  0.7,
                  0.9,
                  0.6,
                  0.35,
                ];
                final base = baseFactors[i];
                final wave = math.sin(
                  _waveController.value * math.pi + (i * 0.45),
                );
                final h = (18 * (base * (0.35 + wave.abs() * 0.65))).clamp(
                  4.0,
                  22.0,
                );

                return Container(
                  width: 3.2,
                  height: h,
                  margin: const EdgeInsets.symmetric(horizontal: 2.5),
                  decoration: BoxDecoration(
                    color: tone.withValues(alpha: 0.8),
                    borderRadius: BorderRadius.circular(2),
                  ),
                );
              }),
            ),

            const SizedBox(height: 12),

            // Clean Minimalist Status Caption
            Text(
              'Translating to ${widget.targetLanguage.name}…',
              style: const TextStyle(
                color: Color(0xFF6B6E64),
                fontSize: 12.5,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.3,
              ),
            ),
          ],
        );
      },
    ),
    );
  }
}

// ---------------------------------------------------------------------------
// Subtle Orbital Shimmer Painter
// ---------------------------------------------------------------------------
class OrbitalShimmerPainter extends CustomPainter {
  OrbitalShimmerPainter({required this.tone});
  final Color tone;

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    // Faint guide orbit
    final orbitPaint = Paint()
      ..color = tone.withValues(alpha: 0.15)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;
    canvas.drawCircle(center, radius, orbitPaint);

    // Glowing satellite bead
    final beadCenter = Offset(center.dx + radius, center.dy);
    final glowPaint = Paint()
      ..color = tone.withValues(alpha: 0.4)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 5);
    canvas.drawCircle(beadCenter, 6, glowPaint);

    final beadPaint = Paint()
      ..color = tone
      ..style = PaintingStyle.fill;
    canvas.drawCircle(beadCenter, 3.5, beadPaint);
  }

  @override
  bool shouldRepaint(covariant OrbitalShimmerPainter oldDelegate) {
    return oldDelegate.tone != tone;
  }
}
