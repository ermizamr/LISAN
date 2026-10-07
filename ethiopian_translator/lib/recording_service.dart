import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

abstract interface class AudioCapture {
  Future<String> start();

  Future<String?> stop();

  Future<void> dispose();
}

class RecordingService implements AudioCapture {
  RecordingService({AudioRecorder? recorder})
    : _recorder = recorder ?? AudioRecorder() {
    _preWarm();
  }

  final AudioRecorder _recorder;
  bool _hasPermission = false;
  String? _cachedTempDir;
  Future<String>? _activeStartFuture;

  Future<void> _preWarm() async {
    try {
      _hasPermission = await _recorder.hasPermission();
      final dir = await getTemporaryDirectory();
      _cachedTempDir = dir.path;
    } catch (_) {}
  }

  @override
  Future<String> start() async {
    if (!_hasPermission) {
      if (!await _recorder.hasPermission()) {
        throw const RecordingException('Microphone permission was denied');
      }
      _hasPermission = true;
    }

    if (_cachedTempDir == null) {
      final dir = await getTemporaryDirectory();
      _cachedTempDir = dir.path;
    }

    final filename = 'lisan_${DateTime.now().microsecondsSinceEpoch}.wav';
    final path = '$_cachedTempDir/$filename';

    final startOp = _recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.wav,
        sampleRate: 16000,
        numChannels: 1,
      ),
      path: path,
    );

    _activeStartFuture = startOp.then((_) => path);
    await startOp;
    return path;
  }

  @override
  Future<String?> stop() async {
    if (_activeStartFuture != null) {
      try {
        await _activeStartFuture;
      } catch (_) {}
      _activeStartFuture = null;
    }
    return _recorder.stop();
  }

  @override
  Future<void> dispose() => _recorder.dispose();
}

class DemoRecordingService implements AudioCapture {
  const DemoRecordingService();

  @override
  Future<String> start() async => '';

  @override
  Future<String?> stop() async => null;

  @override
  Future<void> dispose() async {}
}

class RecordingException implements Exception {
  const RecordingException(this.message);

  final String message;

  @override
  String toString() => 'RecordingException: $message';
}
