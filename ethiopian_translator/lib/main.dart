import 'package:flutter/material.dart';

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
      title: 'Lisan',
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

class _ConversationPageState extends State<ConversationPage> {
  String _source = 'English';
  String _target = 'Amharic';
  bool _recording = false;
  String _status = 'Ready · fully offline';
  final String _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
  final String _formality = 'auto';

  final List<ConversationTurn> _turns = [
    const ConversationTurn(
      source: 'Where is the nearest hospital?',
      translation: 'በአቅራቢያው ያለው ሆስፒታል የት ነው?',
      language: 'English → Amharic',
      isSource: true,
      intent: 'navigation_directions',
      suggestedReplies: [
        QuickReplyItem(text: 'ቅርብ ነው', translation: 'It is close'),
        QuickReplyItem(text: 'በእግር 10 ደቂቃ ይወስዳል', translation: 'It takes 10 minutes walking'),
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

  Future<void> _toggleRecording() async {
    if (_recording) {
      setState(() {
        _recording = false;
        _status = 'Finishing audio...';
      });
      // Keep a short tail so the final syllables are not cut off by the tap.
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
              ? 'Cannot reach ${widget.api.baseUri.host}:${widget.api.baseUri.port} (Tap settings icon ⚙️)'
              : 'Error: ${errStr.length > 50 ? errStr.substring(0, 50) : errStr}';
          setState(() => _status = shortErr);
        }
      }
      return;
    }

    setState(() {
      _recording = true;
      _status = 'Microphone active';
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
          title: const Text('AI Server Settings'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Connect to the local offline translation engine:',
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
              const SizedBox(height: 8),
              Wrap(
                spacing: 6,
                children: [
                  ActionChip(
                    label: const Text('USB (127.0.0.1)'),
                    onPressed: () => setDialogState(() => controller.text = 'http://127.0.0.1:8000'),
                  ),
                  ActionChip(
                    label: const Text('Wi-Fi (10.5.200.137)'),
                    onPressed: () => setDialogState(() => controller.text = 'http://10.5.200.137:8000'),
                  ),
                  ActionChip(
                    label: const Text('Hotspot (192.168.137.1)'),
                    onPressed: () => setDialogState(() => controller.text = 'http://192.168.137.1:8000'),
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
    widget.audioCapture.dispose();
    widget.api.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 20,
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Lisan',
              style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 0.2),
            ),
            Text(
              'Offline conversation translator',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w400),
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
                padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
                itemCount: _turns.length,
                separatorBuilder: (context, index) =>
                    const SizedBox(height: 14),
                itemBuilder: (context, index) => _TurnCard(
                  turn: _turns[index],
                  onQuickReply: _handleQuickReply,
                ),
              ),
            ),
            _RecordPanel(
              recording: _recording,
              status: _status,
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
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Expanded(
            child: _LanguageDropdown(
              label: 'I speak',
              value: source,
              onChanged: (value) => onChanged(value!, target),
            ),
          ),
          IconButton(
            onPressed: () => onChanged(target, source),
            tooltip: 'Swap languages',
            icon: const Icon(Icons.swap_horiz_rounded),
          ),
          Expanded(
            child: _LanguageDropdown(
              label: 'Translate to',
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
            color: Colors.grey.shade600,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
        ),
        DropdownButton<String>(
          value: value,
          isExpanded: true,
          underline: const SizedBox.shrink(),
          icon: const Icon(Icons.keyboard_arrow_down_rounded, size: 18),
          items: _LanguageBar.languages
              .map(
                (language) => DropdownMenuItem(
                  value: language,
                  child: Text(language, overflow: TextOverflow.ellipsis),
                ),
              )
              .toList(),
          onChanged: onChanged,
        ),
      ],
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
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2.5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 11, color: color),
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
    return DecoratedBox(
      decoration: BoxDecoration(
        color: turn.isSource ? const Color(0xFFE1F0EC) : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFD9E3DF)),
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(18, 16, 14, 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text(
                  turn.language,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF167D73),
                  ),
                ),
                const SizedBox(width: 8),
                _buildIntentBadge(turn.intent),
                const Spacer(),
                IconButton(
                  onPressed: () {},
                  tooltip: 'Play translation',
                  icon: const Icon(Icons.volume_up_outlined, size: 20),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              turn.source,
              style: const TextStyle(
                fontSize: 17,
                height: 1.3,
                fontWeight: FontWeight.w600,
              ),
            ),
            const Divider(height: 22),
            Text(
              turn.translation,
              style: const TextStyle(
                fontSize: 19,
                height: 1.35,
                color: Color(0xFF18312F),
              ),
            ),
            if (turn.suggestedReplies.isNotEmpty) ...[
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(
                    Icons.auto_awesome_rounded,
                    size: 13,
                    color: Colors.grey.shade600,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    'Quick Replies',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: Colors.grey.shade600,
                      letterSpacing: 0.2,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Wrap(
                spacing: 8,
                runSpacing: 6,
                children: turn.suggestedReplies.map((reply) {
                  return ActionChip(
                    visualDensity: VisualDensity.compact,
                    backgroundColor: Colors.white,
                    side: BorderSide(
                      color: const Color(0xFF167D73).withValues(alpha: 0.4),
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
    required this.onPressed,
  });

  final bool recording;
  final String status;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 20),
      child: Column(
        children: [
          Text(
            recording ? 'Listening...' : 'Tap to speak',
            style: const TextStyle(
              fontWeight: FontWeight.w700,
              color: Color(0xFF18312F),
            ),
          ),
          const SizedBox(height: 10),
          GestureDetector(
            onTap: onPressed,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              width: 76,
              height: 76,
              decoration: BoxDecoration(
                color: recording
                    ? const Color(0xFFCF5C45)
                    : const Color(0xFF167D73),
                shape: BoxShape.circle,
                boxShadow: [
                  BoxShadow(
                    color:
                        (recording
                                ? const Color(0xFFCF5C45)
                                : const Color(0xFF167D73))
                            .withValues(alpha: 0.25),
                    blurRadius: 16,
                    spreadRadius: 3,
                  ),
                ],
              ),
              child: Icon(
                recording ? Icons.stop_rounded : Icons.mic_rounded,
                color: Colors.white,
                size: 32,
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            status,
            style: const TextStyle(fontSize: 12, color: Color(0xFF66736F)),
          ),
        ],
      ),
    );
  }
}
