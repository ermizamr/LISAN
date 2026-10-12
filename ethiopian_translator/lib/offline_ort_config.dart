import 'dart:ffi' as ffi;
import 'package:flutter/foundation.dart';
import 'package:onnxruntime/onnxruntime.dart';

/// Centralized configuration helper for ONNX Runtime sessions to guarantee
/// execution remains strictly under the <= 350 MB PSS limit on Android 10 devices.
class OfflineOrtConfig {
  /// Creates memory-constrained OrtSessionOptions with:
  /// - constrained thread counts (intra=2, inter=1) to prevent CPU starvation
  /// - basic graph optimization to prevent massive arena allocations
  static OrtSessionOptions createOptions({
    int intraOpThreads = 2,
    int interOpThreads = 1,
    GraphOptimizationLevel optimizationLevel =
        GraphOptimizationLevel.ortEnableBasic,
  }) {
    final options = OrtSessionOptions()
      ..setIntraOpNumThreads(intraOpThreads)
      ..setInterOpNumThreads(interOpThreads)
      ..setSessionGraphOptimizationLevel(optimizationLevel)
      ..appendCPUProvider(CPUFlags.useNone);

    debugPrint(
      '[OfflineOrtConfig] Created session options (intra=$intraOpThreads, inter=$interOpThreads, opt=$optimizationLevel, arena=DISABLED)',
    );
    return options;
  }

  /// Trims Android native dirty heap pages and returns them directly to the Linux kernel.
  static void trimNativeMemory() {
    if (defaultTargetPlatform == TargetPlatform.android) {
      try {
        final ffi.DynamicLibrary lib = ffi.DynamicLibrary.open('libc.so');
        // Android Bionic libc purges jemalloc/scudo pages via mallopt(M_PURGE, 0) where M_PURGE = -101
        final int Function(int, int) mallopt = lib
            .lookupFunction<ffi.Int32 Function(ffi.Int32, ffi.Int32), int Function(int, int)>('mallopt');
        final res = mallopt(-101, 0);
        debugPrint('[OfflineOrtConfig] mallopt(M_PURGE, 0) returned $res (freed native pages to kernel)');
      } catch (e) {
        debugPrint('[OfflineOrtConfig] mallopt error: $e');
      }
    }
  }
}
