import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';

abstract interface class AudioCapture {
  Future<String> start();

  Future<String?> stop();

  Future<void> dispose();
}

class RecordingService implements AudioCapture {
  RecordingService({AudioRecorder? recorder})
    : _recorder = recorder ?? AudioRecorder();

  final AudioRecorder _recorder;

  @override
  Future<String> start() async {
    if (!await _recorder.hasPermission()) {
      throw const RecordingException('Microphone permission was denied');
    }

    final directory = await getTemporaryDirectory();
    final filename = 'lisan_${DateTime.now().microsecondsSinceEpoch}.wav';
    final path = '${directory.path}/$filename';
    await _recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.wav,
        sampleRate: 16000,
        numChannels: 1,
      ),
      path: path,
    );
    return path;
  }

  @override
  Future<String?> stop() => _recorder.stop();

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
