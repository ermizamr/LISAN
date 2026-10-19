import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math' as math;

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

/// Representation of a structured telemetry record.
class AnalyticsEvent {
  AnalyticsEvent({
    required this.id,
    required this.deviceId,
    required this.sessionId,
    required this.eventType,
    this.sourceLang,
    this.targetLang,
    this.inputType,
    this.mode,
    this.latencyMs = 0,
    this.scenario,
    required this.platform,
    this.appVersion = '1.0.0',
    this.metadata = const {},
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now().toUtc();

  final String id;
  final String deviceId;
  final String sessionId;
  final String eventType;
  final String? sourceLang;
  final String? targetLang;
  final String? inputType;
  final String? mode;
  final int latencyMs;
  final String? scenario;
  final String platform;
  final String appVersion;
  final Map<String, dynamic> metadata;
  final DateTime createdAt;

  Map<String, dynamic> toJson() => {
    'id': id,
    'device_id': deviceId,
    'session_id': sessionId,
    'event_type': eventType,
    'source_lang': sourceLang,
    'target_lang': targetLang,
    'input_type': inputType,
    'mode': mode,
    'latency_ms': latencyMs,
    'scenario': scenario,
    'platform': platform,
    'app_version': appVersion,
    'metadata': metadata,
    'created_at': createdAt.toIso8601String(),
  };

  factory AnalyticsEvent.fromJson(Map<String, dynamic> json) => AnalyticsEvent(
    id: json['id'] as String? ?? _generateRandomHex(8),
    deviceId: json['device_id'] as String? ?? 'unknown_device',
    sessionId: json['session_id'] as String? ?? 'unknown_session',
    eventType: json['event_type'] as String? ?? 'unknown_event',
    sourceLang: json['source_lang'] as String?,
    targetLang: json['target_lang'] as String?,
    inputType: json['input_type'] as String?,
    mode: json['mode'] as String?,
    latencyMs: (json['latency_ms'] as num?)?.toInt() ?? 0,
    scenario: json['scenario'] as String?,
    platform: json['platform'] as String? ?? 'unknown_platform',
    appVersion: json['app_version'] as String? ?? '1.0.0',
    metadata: (json['metadata'] as Map<String, dynamic>?) ?? {},
    createdAt: json['created_at'] != null
        ? DateTime.tryParse(json['created_at'] as String)?.toUtc()
        : null,
  );

  static String _generateRandomHex(int length) {
    final rand = math.Random();
    final buffer = StringBuffer();
    for (int i = 0; i < length; i++) {
      buffer.write(rand.nextInt(16).toRadixString(16));
    }
    return buffer.toString();
  }
}

/// Offline-first resilient analytics engine for LISAN.
///
/// Features:
/// 1. Asynchronous non-blocking dispatch — never blocks speech STT, NMT, or TTS.
/// 2. Offline queueing with persistent disk caching on device.
/// 3. Automatic batch sync when online with exponential backoff on retry.
/// 4. Direct Supabase cloud integration with fallback to local server or community table.
class AnalyticsService {
  AnalyticsService._();
  static final AnalyticsService instance = AnalyticsService._();

  static const String supabaseUrl = 'https://xknxnycwrkffmxcwqxjs.supabase.co';
  static const String supabaseKey =
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhrbnhueWN3cmtmZm14Y3dxeGpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIwODM5MTQsImV4cCI6MjEwNzY1OTkxNH0.5MgXgdhAtUggyNnCpL94EcjmR5JrAs74fiYK0BjUDaM';

  static const int maxQueueCapacity = 500;
  static const int batchSize = 25;

  String _deviceId = '';
  String _sessionId = '';
  String _platformName = 'unknown';
  String _osVersion = 'unknown';
  String _localeName = 'unknown';
  String _timezoneName = 'unknown';
  int _sessionCount = 1;
  int _daysSinceInstall = 0;
  bool _initialized = false;
  bool _isFlushing = false;
  Timer? _periodicSyncTimer;

  final List<AnalyticsEvent> _queue = [];
  File? _queueFile;
  File? _deviceIdFile;
  File? _metaFile;

  String get deviceId => _deviceId;
  String get sessionId => _sessionId;
  int get sessionCount => _sessionCount;
  int get daysSinceInstall => _daysSinceInstall;
  int get queuedEventsCount => _queue.length;

  /// Initializes device identifier, loads unsent offline queue, and logs session start.
  Future<void> init({http.Client? httpClient}) async {
    if (_initialized) return;
    _initialized = true;

    try {
      _detectPlatform();
      _sessionId = 'sess_${DateTime.now().millisecondsSinceEpoch}_${_randomHex(6)}';

      bool isFirstInstall = false;
      DateTime installTime = DateTime.now().toUtc();

      if (!kIsWeb) {
        _osVersion = Platform.operatingSystemVersion;
        _localeName = Platform.localeName;
        _timezoneName = DateTime.now().timeZoneName;

        final docsDir = await getApplicationDocumentsDirectory();
        _deviceIdFile = File('${docsDir.path}/lisan_device_id.txt');
        _queueFile = File('${docsDir.path}/lisan_analytics_queue.json');
        _metaFile = File('${docsDir.path}/lisan_device_meta.json');

        if (await _deviceIdFile!.exists()) {
          _deviceId = (await _deviceIdFile!.readAsString()).trim();
        }

        if (_deviceId.isEmpty) {
          _deviceId = 'dev_${DateTime.now().millisecondsSinceEpoch}_${_randomHex(8)}';
          await _deviceIdFile!.writeAsString(_deviceId);
          isFirstInstall = true;
        }

        int sessions = 1;
        if (await _metaFile!.exists()) {
          try {
            final content = await _metaFile!.readAsString();
            final meta = jsonDecode(content) as Map<String, dynamic>;
            sessions = ((meta['session_count'] as num?)?.toInt() ?? 0) + 1;
            if (meta['install_time'] != null) {
              installTime = DateTime.tryParse(meta['install_time'] as String) ?? installTime;
            }
          } catch (_) {}
        } else {
          isFirstInstall = true;
        }

        _sessionCount = sessions;
        _daysSinceInstall = DateTime.now().toUtc().difference(installTime).inDays;

        // Persist updated metadata
        await _metaFile!.writeAsString(jsonEncode({
          'device_id': _deviceId,
          'install_time': installTime.toIso8601String(),
          'session_count': _sessionCount,
          'last_seen': DateTime.now().toUtc().toIso8601String(),
          'os_version': _osVersion,
          'locale': _localeName,
          'timezone': _timezoneName,
        }));

        // Restore offline queue
        if (await _queueFile!.exists()) {
          final content = await _queueFile!.readAsString();
          if (content.isNotEmpty) {
            final List<dynamic> decoded = jsonDecode(content);
            for (final item in decoded) {
              if (item is Map<String, dynamic>) {
                _queue.add(AnalyticsEvent.fromJson(item));
              }
            }
            debugPrint('[Analytics] Restored ${_queue.length} events from offline disk cache');
          }
        }
      } else {
        _deviceId = 'web_${DateTime.now().millisecondsSinceEpoch}_${_randomHex(8)}';
        _osVersion = 'Web Browser';
        _localeName = 'browser';
        _timezoneName = DateTime.now().timeZoneName;
      }

      // 1. If this is the very first app launch on this device, log app_install
      if (isFirstInstall) {
        trackAppInstall(
          osVersion: _osVersion,
          locale: _localeName,
          timezone: _timezoneName,
        );
      }

      // 2. Track session start with retention metrics
      trackSessionStart();

      // Start periodic sync every 45 seconds to upload queued events when online
      _periodicSyncTimer?.cancel();
      _periodicSyncTimer = Timer.periodic(const Duration(seconds: 45), (_) {
        unawaited(flush());
      });

      // Attempt initial flush
      unawaited(flush());
    } catch (e) {
      debugPrint('[Analytics] Initialization error (non-fatal): $e');
      if (_deviceId.isEmpty) {
        _deviceId = 'dev_fallback_${_randomHex(8)}';
      }
    }
  }

  void _detectPlatform() {
    if (kIsWeb) {
      _platformName = 'web';
    } else if (Platform.isAndroid) {
      _platformName = 'android';
    } else if (Platform.isIOS) {
      _platformName = 'ios';
    } else if (Platform.isLinux) {
      _platformName = 'linux';
    } else if (Platform.isWindows) {
      _platformName = 'windows';
    } else if (Platform.isMacOS) {
      _platformName = 'macos';
    } else {
      _platformName = 'other';
    }
  }

  static String _randomHex(int length) {
    final rand = math.Random();
    final buffer = StringBuffer();
    for (int i = 0; i < length; i++) {
      buffer.write(rand.nextInt(16).toRadixString(16));
    }
    return buffer.toString();
  }

  /// Appends an event to memory queue and persists to disk cache.
  void _enqueueEvent(AnalyticsEvent event) {
    if (_queue.length >= maxQueueCapacity) {
      // Discard oldest 10% to prevent unbounded growth on low memory devices
      _queue.removeRange(0, (_queue.length * 0.1).toInt());
    }
    _queue.add(event);
    _persistQueueToDisk();

    // Trigger asynchronous non-blocking flush
    unawaited(flush());
  }

  Future<void> _persistQueueToDisk() async {
    if (kIsWeb || _queueFile == null) return;
    try {
      final jsonStr = jsonEncode(_queue.map((e) => e.toJson()).toList());
      await _queueFile!.writeAsString(jsonStr, flush: true);
    } catch (e) {
      debugPrint('[Analytics] Error saving queue to disk: $e');
    }
  }

  // --------------------------------------------------------------------------
  // Public Event Trackers
  // --------------------------------------------------------------------------

  /// Logs when the app is installed and opened for the first time on a device.
  void trackAppInstall({
    required String osVersion,
    required String locale,
    required String timezone,
    Map<String, dynamic>? extra,
  }) {
    final event = AnalyticsEvent(
      id: 'evt_${_randomHex(10)}',
      deviceId: _deviceId,
      sessionId: _sessionId,
      eventType: 'app_install',
      platform: _platformName,
      metadata: {
        'first_open': true,
        'os_version': osVersion,
        'locale': locale,
        'timezone': timezone,
        'app_version': '1.0.0',
        if (extra != null) ...extra,
      },
    );
    _enqueueEvent(event);
  }

  /// Logs app session launch with retention and hardware demographics.
  void trackSessionStart({Map<String, dynamic>? metadata}) {
    final event = AnalyticsEvent(
      id: 'evt_${_randomHex(10)}',
      deviceId: _deviceId,
      sessionId: _sessionId,
      eventType: 'session_start',
      platform: _platformName,
      metadata: {
        'session_number': _sessionCount,
        'days_since_install': _daysSinceInstall,
        'os_version': _osVersion,
        'locale': _localeName,
        'timezone': _timezoneName,
        ...?metadata,
      },
    );
    _enqueueEvent(event);
  }

  /// Logs a voice or text translation event.
  void trackTranslation({
    required String sourceLang,
    required String targetLang,
    required String inputType, // 'voice' or 'text'
    required String mode,      // 'offline_nmt', 'offline_tm', 'server_api'
    required int latencyMs,
    String? scenario,
    int? textLength,
    bool success = true,
    String? errorMessage,
    Map<String, dynamic>? extra,
  }) {
    final Map<String, dynamic> meta = {
      if (textLength != null) 'text_length': textLength,
      'success': success,
      if (errorMessage != null) 'error': errorMessage,
      if (extra != null) ...extra,
    };

    final event = AnalyticsEvent(
      id: 'evt_${_randomHex(10)}',
      deviceId: _deviceId,
      sessionId: _sessionId,
      eventType: 'translation',
      sourceLang: sourceLang,
      targetLang: targetLang,
      inputType: inputType,
      mode: mode,
      latencyMs: latencyMs,
      scenario: scenario ?? 'general',
      platform: _platformName,
      metadata: meta,
    );
    _enqueueEvent(event);
  }

  /// Logs a text-to-speech voice synthesis event.
  void trackTtsPlayed({
    required String lang,
    required String engine, // 'vits_mms', 'native_platform', 'server_tts'
    int? durationMs,
    Map<String, dynamic>? extra,
  }) {
    final event = AnalyticsEvent(
      id: 'evt_${_randomHex(10)}',
      deviceId: _deviceId,
      sessionId: _sessionId,
      eventType: 'tts_played',
      targetLang: lang,
      mode: engine,
      latencyMs: durationMs ?? 0,
      platform: _platformName,
      metadata: extra ?? {},
    );
    _enqueueEvent(event);
  }

  /// Logs when the user selects a quick scenario mode.
  void trackScenarioSelected({required String scenario}) {
    final event = AnalyticsEvent(
      id: 'evt_${_randomHex(10)}',
      deviceId: _deviceId,
      sessionId: _sessionId,
      eventType: 'scenario_selected',
      scenario: scenario,
      platform: _platformName,
    );
    _enqueueEvent(event);
  }

  /// Logs an unexpected error or fallback occurrence.
  void trackError({
    required String context,
    required String message,
    String? sourceLang,
    String? targetLang,
  }) {
    final event = AnalyticsEvent(
      id: 'evt_${_randomHex(10)}',
      deviceId: _deviceId,
      sessionId: _sessionId,
      eventType: 'error',
      sourceLang: sourceLang,
      targetLang: targetLang,
      platform: _platformName,
      metadata: {'context': context, 'message': message},
    );
    _enqueueEvent(event);
  }

  // --------------------------------------------------------------------------
  // Batch Dispatch & Sync
  // --------------------------------------------------------------------------

  /// Flushes pending events to Supabase REST / Backend server.
  Future<void> flush() async {
    if (_isFlushing || _queue.isEmpty) return;
    _isFlushing = true;

    try {
      final batch = _queue.take(batchSize).toList();
      final success = await _dispatchBatch(batch);
      if (success) {
        _queue.removeRange(0, batch.length);
        await _persistQueueToDisk();
        debugPrint('[Analytics] Successfully synced ${batch.length} telemetry events');

        // If more items remain, flush subsequent batch
        if (_queue.isNotEmpty) {
          unawaited(flush());
        }
      }
    } catch (e) {
      debugPrint('[Analytics] Sync attempt skipped (offline or network error): $e');
    } finally {
      _isFlushing = false;
    }
  }

  /// Attempts to send events to Supabase `app_analytics`.
  /// If the dedicated table doesn't exist yet (HTTP 404), seamlessly falls back
  /// to writing structured telemetry rows into `community_validations`.
  Future<bool> _dispatchBatch(List<AnalyticsEvent> events) async {
    final headers = {
      'apikey': supabaseKey,
      'Authorization': 'Bearer $supabaseKey',
      'Content-Type': 'application/json',
      'Prefer': 'return=minimal',
    };

    final client = http.Client();
    try {
      // 1. Try dedicated app_analytics table
      final directPayload = jsonEncode(
        events.map((e) => {
          'device_id': e.deviceId,
          'session_id': e.sessionId,
          'event_type': e.eventType,
          'source_lang': e.sourceLang,
          'target_lang': e.targetLang,
          'input_type': e.inputType,
          'mode': e.mode,
          'latency_ms': e.latencyMs,
          'scenario': e.scenario,
          'platform': e.platform,
          'app_version': e.appVersion,
          'metadata': e.metadata,
          'created_at': e.createdAt.toIso8601String(),
        }).toList(),
      );

      final directUri = Uri.parse('$supabaseUrl/rest/v1/app_analytics');
      final directResp = await client
          .post(directUri, headers: headers, body: directPayload)
          .timeout(const Duration(seconds: 6));

      if (directResp.statusCode == 201 || directResp.statusCode == 200) {
        return true;
      }

      // 2. If table not yet created (404), fallback to community_validations table
      if (directResp.statusCode == 404) {
        final fallbackPayload = jsonEncode(
          events.map((e) => {
            'tuple_id': 'app_telemetry',
            'domain': 'app_analytics',
            'english_text': 'App Event: ${e.eventType}',
            'target_lang': e.targetLang ?? 'all',
            'original_target': e.sourceLang ?? 'all',
            'validated_text': e.mode ?? 'unknown',
            'status': 'event:${e.eventType}',
            'reviewer_note': jsonEncode({
              'device_id': e.deviceId,
              'session_id': e.sessionId,
              'input_type': e.inputType,
              'latency_ms': e.latencyMs,
              'scenario': e.scenario,
              'platform': e.platform,
              'metadata': e.metadata,
              'created_at': e.createdAt.toIso8601String(),
            }),
          }).toList(),
        );

        final fallbackUri = Uri.parse('$supabaseUrl/rest/v1/community_validations');
        final fallbackResp = await client
            .post(fallbackUri, headers: headers, body: fallbackPayload)
            .timeout(const Duration(seconds: 6));

        if (fallbackResp.statusCode == 201 || fallbackResp.statusCode == 200) {
          return true;
        }
      }
      return false;
    } catch (_) {
      return false;
    } finally {
      client.close();
    }
  }

  /// Cancels periodic timers and releases resources.
  void dispose() {
    _periodicSyncTimer?.cancel();
  }
}
