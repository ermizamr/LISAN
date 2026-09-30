import 'package:audioplayers/audioplayers.dart';
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
  String _selectedScenario = 'all';
  bool _recording = false;
  String _status = 'Ready · fully offline';
  final String _sessionId = 'session_${DateTime.now().millisecondsSinceEpoch}';
  final String _formality = 'auto';

  final AudioPlayer _audioPlayer = AudioPlayer();
  final TextEditingController _textController = TextEditingController();
  String? _currentlyPlayingText;

  @override
  void initState() {
    super.initState();
    _audioPlayer.onPlayerComplete.listen((_) {
      if (mounted) {
        setState(() {
          _currentlyPlayingText = null;
          _status = 'Ready · fully offline';
        });
      }
    });
  }

  Future<void> _playTurnAudio(ConversationTurn turn) async {
    final text = turn.translation.trim();
    if (text.isEmpty) return;

    if (_currentlyPlayingText == text) {
      await _audioPlayer.stop();
      if (mounted) {
        setState(() {
          _currentlyPlayingText = null;
          _status = 'Audio stopped';
        });
      }
      return;
    }

    setState(() {
      _currentlyPlayingText = text;
      _status = 'Speaking translation...';
    });

    try {
      final uri = widget.api.getTtsUri(text, turn.targetLangKey);
      await _audioPlayer.stop();
      await _audioPlayer.play(UrlSource(uri.toString()));
    } catch (e) {
      debugPrint('Audio playback error: $e');
      if (mounted) {
        setState(() {
          _currentlyPlayingText = null;
          _status = 'Audio error: $e';
        });
      }
    }
  }

  final List<ConversationTurn> _turns = [
    const ConversationTurn(
      source: 'Where is the nearest hospital?',
      translation: 'በአቅራቢያው ያለው ሆስፒታል የት ነው?',
      language: 'English → Amharic',
      isSource: true,
      intent: 'emergency_medical',
      suggestedReplies: [
        QuickReplyItem(text: 'ቅርብ ነው', translation: 'It is close'),
        QuickReplyItem(text: 'በእግር 10 ደቂቃ ይወስዳል', translation: 'It takes 10 minutes walking'),
        QuickReplyItem(text: 'ታክሲ ያዝ', translation: 'Take a taxi'),
      ],
      targetLangKey: 'amh',
      confidence: 1.0,
      isTmMatch: true,
      entitiesPreserved: [],
    ),
  ];

  Future<void> _submitText(String text) async {
    final clean = text.trim();
    if (clean.isEmpty) return;
    _textController.clear();

    setState(() {
      _status = 'Translating...';
    });

    try {
      final result = await widget.api.translateText(
        text: clean,
        source: _languageKey(_source),
        target: _languageKey(_target),
        sessionId: _sessionId,
        formality: _formality,
      );
      if (!mounted) return;
      final newTurn = ConversationTurn(
        source: result.sourceText,
        translation: result.translatedText,
        language:
            '${_languageNameFromKey(result.sourceLanguage)} → ${_languageNameFromKey(result.targetLanguage)}',
        isSource: true,
        intent: result.intent,
        suggestedReplies: result.suggestedReplies,
        targetLangKey: result.targetLanguage,
        confidence: result.confidence,
        isTmMatch: result.isTmMatch,
        entitiesPreserved: result.entitiesPreserved,
        warning: result.warning,
      );
      setState(() {
        _turns.add(newTurn);
        _status = 'Ready · ${result.latencySeconds.toStringAsFixed(1)}s';
      });
      _playTurnAudio(newTurn);
    } catch (e) {
      debugPrint('Text translation error: $e');
      if (mounted) {
        setState(() => _status = 'Translation error: $e');
      }
    }
  }

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
            targetLangKey: result.targetLanguage,
            confidence: result.confidence,
            isTmMatch: result.isTmMatch,
            entitiesPreserved: result.entitiesPreserved,
            warning: result.warning,
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
              targetLangKey: result.targetLanguage,
              confidence: result.confidence,
              isTmMatch: result.isTmMatch,
              entitiesPreserved: result.entitiesPreserved,
              warning: result.warning,
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
          targetLangKey: 'amh',
          entitiesPreserved: [],
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

  List<String> _currentStarterPhrases() {
    final langKey = _languageKey(_source);
    final scenario = kScenarios.firstWhere(
      (s) => s.id == _selectedScenario,
      orElse: () => kScenarios.first,
    );
    return scenario.starters[langKey] ?? const [];
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
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
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Lisan',
              style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 0.2),
            ),
            Text(
              'Offline multilingual intelligence',
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
            const SizedBox(height: 10),
            _ScenarioRibbon(
              selectedId: _selectedScenario,
              onSelect: (id) => setState(() => _selectedScenario = id),
            ),
            _StarterPhrasesBar(
              phrases: _currentStarterPhrases(),
              onSelectPhrase: _submitText,
            ),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.fromLTRB(20, 10, 20, 12),
                itemCount: _turns.length,
                separatorBuilder: (context, index) =>
                    const SizedBox(height: 14),
                itemBuilder: (context, index) {
                  final turn = _turns[index];
                  return _TurnCard(
                    turn: turn,
                    onQuickReply: _handleQuickReply,
                    isPlaying: _currentlyPlayingText == turn.translation,
                    onPlay: () => _playTurnAudio(turn),
                  );
                },
              ),
            ),
            _RecordPanel(
              recording: _recording,
              status: _status,
              onPressed: _toggleRecording,
              textController: _textController,
              onTextSubmit: _submitText,
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
    this.targetLangKey = 'orm',
    this.confidence = 0.90,
    this.isTmMatch = false,
    this.entitiesPreserved = const [],
    this.warning,
  });

  final String source;
  final String translation;
  final String language;
  final bool isSource;
  final String intent;
  final List<QuickReplyItem> suggestedReplies;
  final String targetLangKey;
  final double confidence;
  final bool isTmMatch;
  final List<String> entitiesPreserved;
  final String? warning;
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

class _ScenarioRibbon extends StatelessWidget {
  const _ScenarioRibbon({
    required this.selectedId,
    required this.onSelect,
  });

  final String selectedId;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 38,
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        scrollDirection: Axis.horizontal,
        itemCount: kScenarios.length,
        separatorBuilder: (context, index) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final item = kScenarios[index];
          final isSelected = item.id == selectedId;
          return ChoiceChip(
            selected: isSelected,
            avatar: Icon(
              item.icon,
              size: 15,
              color: isSelected ? Colors.white : item.color,
            ),
            label: Text(
              item.label,
              style: TextStyle(
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                color: isSelected ? Colors.white : const Color(0xFF18312F),
              ),
            ),
            selectedColor: item.color,
            backgroundColor: Colors.white,
            side: BorderSide(
              color: isSelected ? item.color : const Color(0xFFD9E3DF),
            ),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
            onSelected: (_) => onSelect(item.id),
          );
        },
      ),
    );
  }
}

class _StarterPhrasesBar extends StatelessWidget {
  const _StarterPhrasesBar({
    required this.phrases,
    required this.onSelectPhrase,
  });

  final List<String> phrases;
  final ValueChanged<String> onSelectPhrase;

  @override
  Widget build(BuildContext context) {
    if (phrases.isEmpty) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.only(top: 8, bottom: 2),
      height: 34,
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        scrollDirection: Axis.horizontal,
        itemCount: phrases.length,
        separatorBuilder: (context, index) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final phrase = phrases[index];
          return ActionChip(
            visualDensity: VisualDensity.compact,
            backgroundColor: const Color(0xFFE8F3F1),
            side: const BorderSide(color: Color(0xFFB4DBD5)),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            label: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.touch_app_rounded,
                  size: 13,
                  color: Color(0xFF167D73),
                ),
                const SizedBox(width: 4),
                Text(
                  phrase,
                  style: const TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF167D73),
                  ),
                ),
              ],
            ),
            onPressed: () => onSelectPhrase(phrase),
          );
        },
      ),
    );
  }
}

class _TurnCard extends StatelessWidget {
  const _TurnCard({
    required this.turn,
    required this.onQuickReply,
    this.onPlay,
    this.isPlaying = false,
  });

  final ConversationTurn turn;
  final ValueChanged<QuickReplyItem> onQuickReply;
  final VoidCallback? onPlay;
  final bool isPlaying;

  Widget _buildIntentBadge(String intent) {
    final (label, icon, color) = switch (intent) {
      'greeting_courtesy' => (
        'Greeting',
        Icons.waving_hand_rounded,
        const Color(0xFF2E7D32),
      ),
      'emergency_medical' || 'medical_health' => (
        'Clinic',
        Icons.local_hospital_rounded,
        const Color(0xFFC62828),
      ),
      'navigation_directions' => (
        'Road',
        Icons.directions_rounded,
        const Color(0xFF0277BD),
      ),
      'dining_hospitality' || 'hospitality_cafe' => (
        'Cafe',
        Icons.coffee_rounded,
        const Color(0xFF6D4C41),
      ),
      'commerce_bargaining' => (
        'Market',
        Icons.storefront_rounded,
        const Color(0xFFE65100),
      ),
      'civic_administration' => (
        'Kebele',
        Icons.account_balance_rounded,
        const Color(0xFF00897B),
      ),
      'banking_finance' => (
        'Bank',
        Icons.payments_rounded,
        const Color(0xFF1E88E5),
      ),
      'education_school' => (
        'School',
        Icons.school_rounded,
        const Color(0xFF5E35B1),
      ),
      'legal_police' => (
        'Police',
        Icons.local_police_rounded,
        const Color(0xFF3949AB),
      ),
      _ => (
        'General',
        Icons.chat_bubble_outline_rounded,
        const Color(0xFF546E7A),
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

  Widget _buildConfidenceBadge() {
    if (turn.isTmMatch) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2.5),
        decoration: BoxDecoration(
          color: const Color(0xFF00796B).withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0xFF00796B).withValues(alpha: 0.3)),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.verified_rounded, size: 11, color: Color(0xFF00796B)),
            SizedBox(width: 3),
            Text(
              'Verified TM',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: Color(0xFF00796B),
              ),
            ),
          ],
        ),
      );
    }

    if (turn.warning != null || turn.confidence < 0.65) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2.5),
        decoration: BoxDecoration(
          color: const Color(0xFFF57F17).withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0xFFF57F17).withValues(alpha: 0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.info_outline_rounded, size: 11, color: Color(0xFFF57F17)),
            const SizedBox(width: 3),
            Text(
              'Approximate (${(turn.confidence * 100).toInt()}%)',
              style: const TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w700,
                color: Color(0xFFF57F17),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2.5),
      decoration: BoxDecoration(
        color: const Color(0xFF1976D2).withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF1976D2).withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.auto_awesome, size: 11, color: Color(0xFF1976D2)),
          const SizedBox(width: 3),
          Text(
            'AI Guard (${(turn.confidence * 100).toInt()}%)',
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: Color(0xFF1976D2),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEntityShieldBadge() {
    if (turn.entitiesPreserved.isEmpty) {
      return const SizedBox.shrink();
    }
    final label = turn.entitiesPreserved.length == 1
        ? 'Shield: ${turn.entitiesPreserved.first}'
        : 'Shielded (${turn.entitiesPreserved.length})';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2.5),
      decoration: BoxDecoration(
        color: const Color(0xFF6A1B9A).withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF6A1B9A).withValues(alpha: 0.3)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.shield_outlined, size: 11, color: Color(0xFF6A1B9A)),
          const SizedBox(width: 3),
          Text(
            label,
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w700,
              color: Color(0xFF6A1B9A),
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
        padding: const EdgeInsets.fromLTRB(18, 14, 14, 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      Text(
                        turn.language,
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF167D73),
                        ),
                      ),
                      _buildIntentBadge(turn.intent),
                      _buildConfidenceBadge(),
                      _buildEntityShieldBadge(),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: onPlay,
                  tooltip: isPlaying ? 'Stop playback' : 'Play translation',
                  icon: Icon(
                    isPlaying ? Icons.volume_up_rounded : Icons.volume_up_outlined,
                    color: isPlaying ? const Color(0xFF167D73) : null,
                    size: 20,
                  ),
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
            if (turn.warning != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF8E1),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFFFFE082)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.lightbulb_outline_rounded, size: 13, color: Color(0xFFF57F17)),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        turn.warning!,
                        style: const TextStyle(
                          fontSize: 11,
                          color: Color(0xFFE65100),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
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
    required this.textController,
    required this.onTextSubmit,
  });

  final bool recording;
  final String status;
  final VoidCallback onPressed;
  final TextEditingController textController;
  final ValueChanged<String> onTextSubmit;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.04),
            blurRadius: 10,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      padding: const EdgeInsets.fromLTRB(16, 10, 16, 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: const Color(0xFFF0F4F3),
                    borderRadius: BorderRadius.circular(24),
                  ),
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: TextField(
                    controller: textController,
                    onSubmitted: onTextSubmit,
                    textInputAction: TextInputAction.send,
                    decoration: const InputDecoration(
                      hintText: 'Type text or tap a starter phrase...',
                      hintStyle: TextStyle(fontSize: 13, color: Color(0xFF8A9A97)),
                      border: InputBorder.none,
                      isDense: true,
                      contentPadding: EdgeInsets.symmetric(vertical: 12),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filled(
                style: IconButton.styleFrom(
                  backgroundColor: const Color(0xFF167D73),
                  foregroundColor: Colors.white,
                ),
                icon: const Icon(Icons.send_rounded, size: 20),
                onPressed: () => onTextSubmit(textController.text),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            recording ? 'Listening...' : 'Tap to speak',
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: Color(0xFF18312F),
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              GestureDetector(
                onTap: onPressed,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  width: 58,
                  height: 58,
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
                            .withValues(alpha: 0.25),
                        blurRadius: 14,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: Icon(
                    recording ? Icons.stop_rounded : Icons.mic_rounded,
                    color: Colors.white,
                    size: 28,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            status,
            style: const TextStyle(fontSize: 11, color: Color(0xFF66736F)),
          ),
        ],
      ),
    );
  }
}

class ScenarioItem {
  const ScenarioItem({
    required this.id,
    required this.label,
    required this.icon,
    required this.color,
    required this.starters,
  });

  final String id;
  final String label;
  final IconData icon;
  final Color color;
  final Map<String, List<String>> starters;
}

const List<ScenarioItem> kScenarios = [
  ScenarioItem(
    id: 'all',
    label: 'All Scenarios',
    icon: Icons.auto_awesome_rounded,
    color: Color(0xFF167D73),
    starters: {},
  ),
  ScenarioItem(
    id: 'emergency_medical',
    label: 'Clinic',
    icon: Icons.local_hospital_rounded,
    color: Color(0xFFC62828),
    starters: {
      'eng': [
        'Where is the nearest hospital or emergency clinic?',
        'I have a severe headache and high fever.',
        'How many times per day should I take this medication?',
      ],
      'amh': [
        'በአቅራቢያው የሚገኝ ክሊኒክ ወይም ሆስፒታል የት ነው?',
        'ከፍተኛ ራስ ምታት እና ትኩሳት አለኝ።',
        'ይህን መድሃኒት በቀን ስንት ጊዜ መውሰድ አለብኝ?',
      ],
      'orm': [
        'Mee hospitaalli ykn kiliniikiin dhihoo eessa jira?',
        'Dhibee mataa fi bowwoo cimaan na qabeera.',
        'Qoricha kana guyyaatti yeroo meeqa fudhachuu qaba?',
      ],
      'tir': [
        'በጃኹም ዝቐረበ ሆስፒታል ወይ ክሊኒክ ኣበይ ኣሎ?',
        'ብርቱዕ ርእሲ ሕማምን ረስንን ኣለኒ።',
        'ነዚ ፈውሲ ኣብ መዓልቲ ክንደይ ሳዕ ክወስዶ ኣለኒ?',
      ],
      'som': [
        'Xaggee bay ku taallaa rugta caafimaadka ee ugu dhow?',
        'Waxaa i haya madax-xanuun daran iyo qandho sare.',
        'Daawadan maalintii imisa jeer ayaan qaadanayaa?',
      ],
    },
  ),
  ScenarioItem(
    id: 'navigation_directions',
    label: 'Road',
    icon: Icons.directions_rounded,
    color: Color(0xFF0277BD),
    starters: {
      'eng': [
        'Which minibus goes toward the city center?',
        'Please drop me off right at the roundabout.',
        'How much is the regular fare per passenger?',
      ],
      'amh': [
        'ወደ መሀል ከተማ የሚሄደው ሚኒባስ ታክሲ የትኛው ነው?',
        'እባክዎን አደባባዩ ጋር አውርዱኝ።',
        'የአንድ ሰው የታክሲ ታሪፍ ስንት ብር ነው?',
      ],
      'orm': [
        'Mee miniibaasiin gara giddugala magaalaa deemu isa kam?',
        'Mee asuma naannoo roondiitti na buusaa.',
        'Gatiin taaksii nama tokkoo meeqa?',
      ],
      'tir': [
        'ናብ ማእከል ከተማ ዝኸይድ ሚኒባስ ታክሲ ኣየናይ እዩ?',
        'በጃኹም ኣብቲ ኣደባባይ ኣውርዱኒ።',
        'ናይ ሓደ ሰብ ናይ ታክሲ ክፍሊት ክንደይ እዩ?',
      ],
      'som': [
        'Koolbiyada u socota bartamaha magaalada ma tan baa?',
        'Fadlan igu daji wareega wadada horteeda.',
        'Lacagta qofka raaca baska waa imisa?',
      ],
    },
  ),
  ScenarioItem(
    id: 'hospitality_cafe',
    label: 'Cafe',
    icon: Icons.coffee_rounded,
    color: Color(0xFF6D4C41),
    starters: {
      'eng': [
        'Please brew two cups of traditional clay-pot coffee.',
        'A macchiato with low sugar, please.',
        'Could we please have our bill calculation?',
      ],
      'amh': [
        'እባክዎን ሁለት ስኒ የጀበና ቡና አፍሉልን።',
        'ስኳር የቀነሰ ማኪያቶ እባክዎን።',
        'እባክዎን ሂሳባችንን አስሉልን።',
      ],
      'orm': [
        'Mee buna jabanaa siinii lama nuuf dafaatii affeelaa.',
        'Mee makiyoatoo sukkaara qallabaa nuuf kennaa.',
        'Mee herrega keenya nuuf shallagaa.',
      ],
      'tir': [
        'በጃኹም ክልተ ፍንጃል ናይ ጀበና ቡን ኣፍልሑልና።',
        'ሽኮር ዝነከየ ማኪያቶ በጃኹም።',
        'በጃኹም ሕሳብና ጸባጽቡልና።',
      ],
      'som': [
        'Fadlan noo kari laba koob oo bun dhaqameed ah.',
        'I sii macchiato sonkortu ku yar tahay.',
        'Fadlan xisaabta noo keen.',
      ],
    },
  ),
  ScenarioItem(
    id: 'commerce_bargaining',
    label: 'Market',
    icon: Icons.storefront_rounded,
    color: Color(0xFFE65100),
    starters: {
      'eng': [
        'How much is this per kilogram? Can you give a discount?',
        'Tell me your final rock-bottom price.',
        'Please weigh three kilograms on the scale.',
      ],
      'amh': [
        'የዚህ ዋጋ በኪሎ ስንት ነው? ቅናሽ ታደርጋለህ?',
        'እባክህ የመጨረሻውን ዋጋ ቁረጥልኝ።',
        'በሚዛኑ ሶስት ኪሎ መዝንልኝ።',
      ],
      'orm': [
        'Wanti kun gatiin isaa meeqa? Hir\'isuu ni dandeessuu?',
        'Mee gatii dhumaa natti himi.',
        'Mee miizaana irratti kiiloo sadii naaf madaali.',
      ],
      'tir': [
        'ዋጋ ናይዚ ብኪሎ ክንደይ እዩ? ክትንክዩለይ ትኽእሉዶ?',
        'በጃኹም ናይ መወዳእታ ዋጋ ቁረጹለይ።',
        'ኣብ ሚዛን ሰለስተ ኪሎ መዝኑለይ።',
      ],
      'som': [
        'Alaabtan kiiladeedu waa imisa? Qiimo dhimis ma ii samayn kartaa?',
        'Ii sheeg qiimaha ugu dambeeya ee aad ku goynayso.',
        'Fadlan miisaanka iigu saar saddex kiilo.',
      ],
    },
  ),
  ScenarioItem(
    id: 'civic_administration',
    label: 'Kebele',
    icon: Icons.account_balance_rounded,
    color: Color(0xFF00897B),
    starters: {
      'eng': [
        'What documents are required to renew my expired resident ID?',
        'Can you stamp and verify this official agreement?',
        'Where do I register for the national digital ID?',
      ],
      'amh': [
        'የቀበሌ መታወቂያዬን ለማደስ ምን ማስረጃዎች ያስፈልጋሉ?',
        'በዚህ ውል ላይ የቀበሌ ማህተም እና ፊርማ ታደርጉልኛላችሁ?',
        'የፋይዳ ብሔራዊ ዲጂታል መታወቂያ የት ነው የሚመዘገበው?',
      ],
      'orm': [
        'Waraqaa eenyummaa koo haareffachuuf sanadoota akkamiitu barbaachisa?',
        'Sanada kana irratti chaappaa rasmigaa fi mallattoo naaf gootuu?',
        'Eenyummaa biyyoolessaa Faydaa eessatti galmeeffanna?',
      ],
      'tir': [
        'ናይ ቀበሌ መንነት ወረቐተይ ንምሕዳስ እንታይ መርትዖታት የድልዩኒ?',
        'ኣብዚ ሰነድ ናይ ቀበሌ ማሕተምን ፊርማን ከተዕርፉለይ ትኽእሉዶ?',
        'ናይ ፋይዳ ሃገራዊ ዲጂታል መንነት ኣበይ ይምዝገብ?',
      ],
      'som': [
        'Waa maxay dukumentiyada looga baahan yahay cusboonaysiinta aqoonsiga?',
        'Ma ku dhufan kartaa shaabadda xaafadda iyo saxiixa warqaddan?',
        'Xaggee baan iska diiwaangeliyaa aqoonsiga Fayda?',
      ],
    },
  ),
  ScenarioItem(
    id: 'banking_finance',
    label: 'Bank',
    icon: Icons.payments_rounded,
    color: Color(0xFF1E88E5),
    starters: {
      'eng': [
        'I want to deposit cash into my savings account.',
        'Can I link this account to mobile banking and Telebirr?',
        'My ATM card was swallowed by the machine yesterday.',
      ],
      'amh': [
        'ወደ ቁጠባ ሂሳቤ ጥሬ ገንዘብ ማስገባት እፈልጋለሁ።',
        'ይህንን የባንክ ሂሳብ ከሞባይል ባንኪንግ እና ቴሌብር ጋር ማገናኘት እችላለሁ?',
        'ትናንት ማታ የኤቲኤም ካርዴ ማሽን ውስጥ ተውጦብኛል።',
      ],
      'orm': [
        'Herrega qusannaa koo keessatti maallaqa callaa galchuu nan barbaada.',
        'Herrega kana moobaayil baankiingii fi Telebirr waliin walitti hidhuu nan danda\'aa?',
        'Galgala kaleessaa kaardiin eetiyeemii koo maashinatti na jalaa liqimfameera.',
      ],
      'tir': [
        'ናብ ናይ ምድላው ሕሳበይ ጥረ ገንዘብ ከእቱ እደሊ ኣለኹ።',
        'ነዚ ናይ ባንክ ሕሳበይ ምስ ሞባይል ባንኪንግን ቴሌብርን ከተሓሕዞ እኽእልዶ?',
        'ትማሊ ምሸት ናይ ኤቲኤም ካርደይ ኣብዚ ማሽን ተወሒጡኒ።',
      ],
      'som': [
        'Waxaan rabaa inaan lacag caddaan ah ku shubo akoonkayga kaydka.',
        'Ma ku xiri karaa akoonkan bangiga moobilka iyo Telebirr?',
        'Xalay kaarkaygii ATM-ka waxaa liqay mashiinka.',
      ],
    },
  ),
  ScenarioItem(
    id: 'education_school',
    label: 'School',
    icon: Icons.school_rounded,
    color: Color(0xFF5E35B1),
    starters: {
      'eng': [
        'Where is the registrar\'s office and tuition payment window?',
        'Until when is the course add-drop deadline this semester?',
        'I need an official student transcript copy with an institutional seal.',
      ],
      'amh': [
        'የሬጅስትራር ቢሮ እና የትምህርት ክፍያ መስኮት የት ይገኛል?',
        'የኮርስ አድ-ድሮፕ ምዝገባ ማብቂያ እስከ መቼ ነው?',
        'የዲግሪ ምስክር ወረቀቴን እና ይፋዊ የትራንስክሪፕት ቅጅ እፈልጋለሁ።',
      ],
      'orm': [
        'Biiroo rejistiraaraa fi kaffaltii barumsaa eessatti argadha?',
        'Guyyaan xumuraa kourse add-drop semisteera kanaa yoomi?',
        'Waraqaa ragaa digirii fi kooppii tiraanskiriiptii barbaada.',
      ],
      'tir': [
        'ናይ ሬጅስትራር ቢሮን ናይ ክፍሊት መስኮትን ኣበይ ይርከብ?',
        'ናይዚ ሰሚስተር ናይ ኣድ-ድሮፕ ናይ መወዳእታ ግዜ ክሳብ መዓስ እዩ?',
        'ናይ ዲግሪ ምስክር ወረቐተይን ወግዓዊ ትራንስክሪፕትን እደሊ ኣለኹ።',
      ],
      'som': [
        'Xaggee ku yaallaa xafiiska diiwaangelinta iyo lacag-bixinta?',
        'Ilaa goormaa soconaysa waqtiga koorsooyinka lagu daro ama laga saaro?',
        'Waxaan u baahanahay shahaadadaydii iyo koobiga rasmiga ah ee buundooyinka.',
      ],
    },
  ),
  ScenarioItem(
    id: 'legal_police',
    label: 'Police',
    icon: Icons.local_police_rounded,
    color: Color(0xFF3949AB),
    starters: {
      'eng': [
        'I need to file a formal police report regarding a burglary.',
        'Can we resolve this neighbor dispute through peaceful mediation?',
        'Can you provide a police verification letter for my bank and passport?',
      ],
      'amh': [
        'የስርቆት ወንጀል አቤቱታ ለፖሊስ ማስመዝገብ እፈልጋለሁ።',
        'ይህንን የጎረቤት ክርክር በሽምግልና እና በሰላም መፍታት እንችላለን?',
        'ፓስፖርት ለማሳገድ እና ለባንክ የሚሆን የፖሊስ ደብዳቤ ትሰጡኛላችሁ?',
      ],
      'orm': [
        'Manni koo waan hatameef iyyannoo yakkaa galmeessuun barbaada.',
        'Walitti bu\'iinsa daangaa ollaa keenya jaarsummaan fixuu dandeenyaa?',
        'Paaspoortii ugguruuf xalayaa ragaa poolisii naaf kennuu dandeessuu?',
      ],
      'tir': [
        'ናይ ስርቂ ገበን ጥርዓን ናብ ፖሊስ ከእቱ እደሊ ኣለኹ።',
        'ነዚ ናይ ወሰን ባእሲ ብሽምግልናን ብሰላምን ክንፈትሖ ንኽእልዶ?',
        'ፓስፖርት ንምእጋድን ንባንክን ናይ ፖሊስ መርትዖ ደብዳበ ክትህቡኒ ትኽእሉዶ?',
      ],
      'som': [
        'Waxaan rabaa inaan diiwaangeliyo dacwad rasmi ah oo ku saabsan tuugo.',
        'Murankan deriska miyaan ku xallin karnaa dhex-dhexaadin iyo nabad?',
        'Ma i siin kartaa warqad xaqiijin ah oo booliis ah oo loogu talagalay bangiga?',
      ],
    },
  ),
];
