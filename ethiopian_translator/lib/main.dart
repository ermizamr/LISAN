import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'recording_service.dart';
import 'translator_api.dart';

void main() => runApp(
  TranslatorApp(audioCapture: RecordingService(), api: TranslatorApi()),
);

class TranslatorApp extends StatelessWidget {
  const TranslatorApp({super.key, this.audioCapture, this.api});

  final AudioCapture? audioCapture;
  final TranslatorApi? api;

  @override
  Widget build(BuildContext context) {
    const ink = Color(0xFF18312F);
    return MaterialApp(
      title: 'Lisan - Horn of Africa Translator',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF167D73),
          brightness: Brightness.light,
          surface: const Color(0xFFF7F5EF),
        ),
        scaffoldBackgroundColor: const Color(0xFFF7F5EF),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFFF7F5EF),
          foregroundColor: ink,
          elevation: 0,
        ),
        fontFamily: 'sans',
        useMaterial3: true,
      ),
      home: ConversationPage(audioCapture: audioCapture, api: api),
    );
  }
}

class ConversationPage extends StatefulWidget {
  ConversationPage({super.key, AudioCapture? audioCapture, TranslatorApi? api})
    : audioCapture = audioCapture ?? const DemoRecordingService(),
      api = api ?? TranslatorApi();

  final AudioCapture audioCapture;
  final TranslatorApi api;

  @override
  State<ConversationPage> createState() => _ConversationPageState();
}

class _ConversationPageState extends State<ConversationPage> with SingleTickerProviderStateMixin {
  String _source = 'English';
  String _target = 'Amharic';
  bool _recording = false;
  String _status = 'Ready · 100% Offline AI';
  final String _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
  final String _formality = 'auto';
  final TextEditingController _textController = TextEditingController();
  late final AnimationController _pulseController = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1200),
  )..repeat(reverse: true);

  final List<ConversationTurn> _turns = [
    const ConversationTurn(
      source: 'Where is the nearest hospital?',
      translation: 'በአቅራቢያው ያለው ሆስፒታል የት ነው?',
      language: 'English → Amharic',
      isSource: true,
      intent: 'navigation_directions',
      suggestedReplies: [
        QuickReplyItem(text: 'ቅርብ ነው', translation: 'It is close'),
        QuickReplyItem(text: 'በእግር 10 ደቂቃ ይወስዳል', translation: 'It takes 10 mins walk'),
        QuickReplyItem(text: 'ታክሲ ያዝ', translation: 'Take a taxi'),
      ],
    ),
  ];

  Future<void> _handleQuickReply(QuickReplyItem reply) async {
    setState(() {
      _status = 'Translating reply...';
    });
    try {
      final result = await widget.api.translateText(
        text: reply.text,
        source: _languageKey(_target),
        target: _languageKey(_source),
        sessionId: _sessionId,
        formality: _formality,
      );
      if (!mounted) return;
      setState(() {
        final srcDisplay = _languageNameFromKey(result.sourceLanguage);
        final tgtDisplay = _languageNameFromKey(result.targetLanguage);
        _turns.add(
          ConversationTurn(
            source: result.sourceText,
            translation: result.translatedText,
            language: '$srcDisplay → $tgtDisplay',
            isSource: false,
            intent: result.intent,
            suggestedReplies: result.suggestedReplies,
          ),
        );
        _status = 'Ready · ${result.latencySeconds.toStringAsFixed(1)}s';
      });
    } catch (e) {
      debugPrint('Quick reply error: $e');
      if (mounted) {
        setState(() => _status = 'Reply error: $e');
      }
    }
  }

  Future<void> _submitText() async {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    _textController.clear();
    setState(() {
      _status = 'Translating text...';
    });

    try {
      final result = await widget.api.translateText(
        text: text,
        source: _languageKey(_source),
        target: _languageKey(_target),
        sessionId: _sessionId,
        formality: _formality,
      );
      if (!mounted) return;
      setState(() {
        final srcDisplay = _languageNameFromKey(result.sourceLanguage);
        final tgtDisplay = _languageNameFromKey(result.targetLanguage);
        _turns.add(
          ConversationTurn(
            source: result.sourceText,
            translation: result.translatedText,
            language: '$srcDisplay → $tgtDisplay',
            isSource: true,
            intent: result.intent,
            suggestedReplies: result.suggestedReplies,
          ),
        );
        _status = 'Ready · ${result.latencySeconds.toStringAsFixed(1)}s';
      });
    } catch (e) {
      debugPrint('Text translation error: $e');
      if (mounted) {
        setState(() => _status = 'Error connecting to AI server');
      }
    }
  }

  Future<void> _toggleRecording() async {
    if (_recording) {
      setState(() {
        _recording = false;
        _status = 'Processing voice audio...';
      });
      await Future<void>.delayed(const Duration(milliseconds: 300));
      final path = await widget.audioCapture.stop();
      if (!mounted) return;

      if (path == null || path.isEmpty) {
        _addDemoTurn();
        return;
      }

      try {
        final result = await widget.api.translateAudio(
          filePath: path,
          source: _languageKey(_source),
          target: _languageKey(_target),
          sessionId: _sessionId,
          formality: _formality,
        );
        if (!mounted) return;
        setState(() {
          final srcDisplay = _languageNameFromKey(result.sourceLanguage);
          final tgtDisplay = _languageNameFromKey(result.targetLanguage);
          _turns.add(
            ConversationTurn(
              source: result.sourceText,
              translation: result.translatedText,
              language: '$srcDisplay → $tgtDisplay',
              isSource: true,
              intent: result.intent,
              suggestedReplies: result.suggestedReplies,
            ),
          );
          _status = 'Ready · ${result.latencySeconds.toStringAsFixed(1)}s';
        });
      } catch (e) {
        debugPrint('Audio translation error: $e');
        if (mounted) {
          final errStr = e.toString();
          final shortErr = errStr.contains('SocketException')
              ? 'Cannot reach AI server (Tap ⚙️ settings)'
              : 'Error: ${errStr.length > 40 ? errStr.substring(0, 40) : errStr}';
          setState(() => _status = shortErr);
        }
      }
      return;
    }

    setState(() {
      _recording = true;
      _status = 'Listening... Speak clearly';
    });
    try {
      await widget.audioCapture.start();
    } catch (e) {
      debugPrint('Audio recording error: $e');
      if (mounted) {
        setState(() {
          _recording = false;
          _status = 'Microphone permission required';
        });
      }
    }
  }

  void _showSettingsDialog() {
    final controller = TextEditingController(text: widget.api.baseUri.toString());
    String testStatus = '';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Row(
            children: [
              Icon(Icons.settings_input_antenna_rounded, color: Color(0xFF167D73)),
              SizedBox(width: 8),
              Text('AI Server Settings'),
            ],
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Connect to local offline translation engine:',
                style: TextStyle(fontSize: 13),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: controller,
                decoration: const InputDecoration(
                  labelText: 'Server URL',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 6,
                children: [
                  ActionChip(
                    label: const Text('Emulator (127.0.0.1)'),
                    onPressed: () => setDialogState(() => controller.text = 'http://127.0.0.1:8000'),
                  ),
                  ActionChip(
                    label: const Text('Localhost'),
                    onPressed: () => setDialogState(() => controller.text = 'http://localhost:8000'),
                  ),
                ],
              ),
              if (testStatus.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text(
                  testStatus,
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: testStatus.contains('Connected') ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () async {
                setDialogState(() => testStatus = 'Testing connection...');
                try {
                  final uri = Uri.parse(controller.text.trim());
                  widget.api.baseUri = uri;
                  final ready = await widget.api.isReady();
                  setDialogState(() {
                    testStatus = ready ? '✓ Connected! Server ready.' : 'Server loading...';
                  });
                } catch (e) {
                  setDialogState(() => testStatus = 'Connection failed: $e');
                }
              },
              child: const Text('Test Connection'),
            ),
            FilledButton(
              style: FilledButton.styleFrom(backgroundColor: const Color(0xFF167D73)),
              onPressed: () {
                final uri = Uri.tryParse(controller.text.trim());
                if (uri != null) {
                  widget.api.baseUri = uri;
                  setState(() => _status = 'Connected to ${uri.host}');
                }
                Navigator.pop(ctx);
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

  void _addDemoTurn() {
    setState(() {
      _turns.add(
        const ConversationTurn(
          source: 'I need help, please.',
          translation: 'እባክዎ እርዳታ እፈልጋለሁ።',
          language: 'English → Amharic',
          isSource: true,
        ),
      );
      _status = 'Ready · demo mode';
    });
  }

  String _languageKey(String language) {
    const keys = {
      'English': 'eng',
      'Amharic': 'amh',
      'Afaan Oromo': 'orm',
      'Somali': 'som',
      'Tigrinya': 'tir',
    };
    return keys[language]!;
  }

  String _languageNameFromKey(String key) {
    const names = {
      'eng': 'English',
      'amh': 'Amharic',
      'orm': 'Afaan Oromo',
      'som': 'Somali',
      'tir': 'Tigrinya',
    };
    return names[key] ?? key;
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _textController.dispose();
    widget.audioCapture.dispose();
    widget.api.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 20,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFF167D73).withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(Icons.translate_rounded, color: Color(0xFF167D73), size: 22),
            ),
            const SizedBox(width: 12),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Lisan (ልሳን)',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 18, letterSpacing: 0.2),
                ),
                Text(
                  'Offline Horn of Africa Translator',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, color: Color(0xFF546E7A)),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: _showSettingsDialog,
            tooltip: 'Server settings',
            icon: const Icon(Icons.tune_rounded),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 4),
            _LanguageBar(
              source: _source,
              target: _target,
              onChanged: (source, target) {
                setState(() {
                  _source = source;
                  _target = target;
                });
              },
            ),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 16),
                itemCount: _turns.length,
                separatorBuilder: (context, index) => const SizedBox(height: 16),
                itemBuilder: (context, index) => _TurnCard(
                  turn: _turns[index],
                  onQuickReply: _handleQuickReply,
                ),
              ),
            ),
            _TextInputBar(
              controller: _textController,
              onSubmitted: _submitText,
            ),
            _RecordPanel(
              recording: _recording,
              status: _status,
              pulseAnimation: _pulseController,
              onPressed: _toggleRecording,
            ),
          ],
        ),
      ),
    );
  }
}

class ConversationTurn {
  const ConversationTurn({
    required this.source,
    required this.translation,
    required this.language,
    required this.isSource,
    this.intent = 'general_conversation',
    this.suggestedReplies = const [],
  });

  final String source;
  final String translation;
  final String language;
  final bool isSource;
  final String intent;
  final List<QuickReplyItem> suggestedReplies;
}

class _LanguageBar extends StatelessWidget {
  const _LanguageBar({
    required this.source,
    required this.target,
    required this.onChanged,
  });

  final String source;
  final String target;
  final void Function(String, String) onChanged;
  static const languages = [
    'English',
    'Amharic',
    'Afaan Oromo',
    'Somali',
    'Tigrinya',
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: _LanguageDropdown(
              label: 'From',
              value: source,
              onChanged: (value) => onChanged(value!, target),
            ),
          ),
          Container(
            decoration: BoxDecoration(
              color: const Color(0xFF167D73).withValues(alpha: 0.08),
              shape: BoxShape.circle,
            ),
            child: IconButton(
              onPressed: () => onChanged(target, source),
              tooltip: 'Swap languages',
              icon: const Icon(Icons.swap_horiz_rounded, color: Color(0xFF167D73)),
            ),
          ),
          Expanded(
            child: _LanguageDropdown(
              label: 'To',
              value: target,
              onChanged: (value) => onChanged(source, value!),
            ),
          ),
        ],
      ),
    );
  }
}

class _LanguageDropdown extends StatelessWidget {
  const _LanguageDropdown({
    required this.label,
    required this.value,
    required this.onChanged,
  });

  final String label;
  final String value;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: TextStyle(
            color: Colors.grey.shade500,
            fontSize: 10,
            fontWeight: FontWeight.w700,
            letterSpacing: 0.5,
          ),
        ),
        DropdownButton<String>(
          value: value,
          isExpanded: true,
          underline: const SizedBox.shrink(),
          icon: const Icon(Icons.keyboard_arrow_down_rounded, size: 18, color: Color(0xFF167D73)),
          items: _LanguageBar.languages
              .map(
                (language) => DropdownMenuItem(
                  value: language,
                  child: Text(
                    language,
                    style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              )
              .toList(),
          onChanged: onChanged,
        ),
      ],
    );
  }
}

class _TextInputBar extends StatelessWidget {
  const _TextInputBar({
    required this.controller,
    required this.onSubmitted,
  });

  final TextEditingController controller;
  final VoidCallback onSubmitted;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFD9E3DF)),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'Type text to translate...',
                border: InputBorder.none,
                isDense: true,
                hintStyle: TextStyle(fontSize: 13, color: Colors.grey),
              ),
              onSubmitted: (_) => onSubmitted(),
            ),
          ),
          IconButton(
            onPressed: onSubmitted,
            icon: const Icon(Icons.send_rounded, color: Color(0xFF167D73), size: 20),
            tooltip: 'Translate text',
          ),
        ],
      ),
    );
  }
}

class _TurnCard extends StatelessWidget {
  const _TurnCard({
    required this.turn,
    required this.onQuickReply,
  });

  final ConversationTurn turn;
  final ValueChanged<QuickReplyItem> onQuickReply;

  Widget _buildIntentBadge(String intent) {
    final (label, icon, color) = switch (intent) {
      'greeting_courtesy' => (
        'Greeting',
        Icons.waving_hand_rounded,
        const Color(0xFF2E7D32)
      ),
      'commerce_bargaining' => (
        'Shopping',
        Icons.storefront_rounded,
        const Color(0xFFE65100)
      ),
      'navigation_directions' => (
        'Directions',
        Icons.directions_rounded,
        const Color(0xFF0277BD)
      ),
      'dining_hospitality' => (
        'Dining',
        Icons.restaurant_rounded,
        const Color(0xFFAD1457)
      ),
      'emergency_medical' => (
        'Emergency',
        Icons.local_hospital_rounded,
        const Color(0xFFC62828)
      ),
      _ => (
        'Conversation',
        Icons.chat_bubble_outline_rounded,
        const Color(0xFF546E7A)
      ),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.25)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: color),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: turn.isSource ? const Color(0xFFE8F3F0) : Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: turn.isSource ? const Color(0xFFC2DCD6) : const Color(0xFFE0E6E4),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 16, 16, 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  turn.language,
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF167D73),
                    letterSpacing: 0.3,
                  ),
                ),
                const SizedBox(width: 8),
                _buildIntentBadge(turn.intent),
                const Spacer(),
                IconButton(
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: turn.translation));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Copied translation to clipboard'),
                        duration: Duration(seconds: 1),
                      ),
                    );
                  },
                  tooltip: 'Copy translation',
                  icon: const Icon(Icons.copy_rounded, size: 18, color: Color(0xFF546E7A)),
                  constraints: const BoxConstraints(),
                  padding: EdgeInsets.zero,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              turn.source,
              style: TextStyle(
                fontSize: 15,
                height: 1.3,
                fontWeight: FontWeight.w500,
                color: Colors.grey.shade700,
              ),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 10),
              child: Divider(height: 1, color: Color(0xFFE0E6E4)),
            ),
            Text(
              turn.translation,
              style: const TextStyle(
                fontSize: 18,
                height: 1.35,
                fontWeight: FontWeight.w700,
                color: Color(0xFF18312F),
              ),
            ),
            if (turn.suggestedReplies.isNotEmpty) ...[
              const SizedBox(height: 14),
              Row(
                children: [
                  const Icon(
                    Icons.auto_awesome_rounded,
                    size: 13,
                    color: Color(0xFF167D73),
                  ),
                  const SizedBox(width: 4),
                  const Text(
                    'Quick Replies',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF167D73),
                      letterSpacing: 0.2,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: turn.suggestedReplies.map((reply) {
                  return ActionChip(
                    visualDensity: VisualDensity.compact,
                    backgroundColor: Colors.white,
                    side: BorderSide(
                      color: const Color(0xFF167D73).withValues(alpha: 0.35),
                    ),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    label: Text(
                      reply.text,
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF167D73),
                      ),
                    ),
                    tooltip: reply.translation.isNotEmpty
                        ? reply.translation
                        : null,
                    onPressed: () => onQuickReply(reply),
                  );
                }).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _RecordPanel extends StatelessWidget {
  const _RecordPanel({
    required this.recording,
    required this.status,
    required this.pulseAnimation,
    required this.onPressed,
  });

  final bool recording;
  final String status;
  final Animation<double> pulseAnimation;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
      child: Column(
        children: [
          Text(
            recording ? 'Listening... Tap to stop' : 'Tap to speak',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 13,
              color: recording ? const Color(0xFFCF5C45) : const Color(0xFF18312F),
            ),
          ),
          const SizedBox(height: 10),
          GestureDetector(
            onTap: onPressed,
            child: AnimatedBuilder(
              animation: pulseAnimation,
              builder: (context, child) {
                final scale = recording ? 1.0 + (pulseAnimation.value * 0.15) : 1.0;
                return Transform.scale(
                  scale: scale,
                  child: Container(
                    width: 72,
                    height: 72,
                    decoration: BoxDecoration(
                      color: recording
                          ? const Color(0xFFCF5C45)
                          : const Color(0xFF167D73),
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          color: (recording
                                  ? const Color(0xFFCF5C45)
                                  : const Color(0xFF167D73))
                              .withValues(alpha: recording ? 0.4 : 0.25),
                          blurRadius: recording ? 20 : 12,
                          spreadRadius: recording ? 6 : 2,
                        ),
                      ],
                    ),
                    child: Icon(
                      recording ? Icons.stop_rounded : Icons.mic_rounded,
                      color: Colors.white,
                      size: 32,
                    ),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: 8),
          Text(
            status,
            style: const TextStyle(fontSize: 11, color: Color(0xFF66736F), fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}
