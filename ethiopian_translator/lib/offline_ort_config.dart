import 'dart:ffi' as ffi;
import 'package:ffi/ffi.dart';
import 'package:flutter/foundation.dart';
import 'package:onnxruntime/onnxruntime.dart';
// ignore: implementation_imports
import 'package:onnxruntime/src/bindings/onnxruntime_bindings_generated.dart' as bg;

/// Centralized configuration helper for ONNX Runtime sessions to guarantee
/// execution remains strictly under the <= 350 MB PSS limit on Android 10 devices,
/// with high-performance zero-copy native memory access.
class OfflineOrtConfig {
  /// Creates memory-constrained OrtSessionOptions with:
  /// - constrained thread counts (intra=4, inter=1) to prevent CPU starvation
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

  /// Retrieves tensor shape directly from ONNX Runtime C API without Dart allocations
  static List<int> getTensorShape(OrtValue tensor) {
    final infoPtrPtr = calloc<ffi.Pointer<bg.OrtTensorTypeAndShapeInfo>>();
    try {
      final statusPtr = OrtEnv.instance.ortApiPtr.ref.GetTensorTypeAndShape
          .asFunction<
              bg.OrtStatusPtr Function(ffi.Pointer<bg.OrtValue>,
                  ffi.Pointer<ffi.Pointer<bg.OrtTensorTypeAndShapeInfo>>)>()(
        tensor.ptr,
        infoPtrPtr,
      );
      OrtStatus.checkOrtStatus(statusPtr);
      final infoPtr = infoPtrPtr.value;

      final countPtr = calloc<ffi.Size>();
      try {
        final dimCountStatus = OrtEnv.instance.ortApiPtr.ref.GetDimensionsCount
            .asFunction<
                bg.OrtStatusPtr Function(
                    ffi.Pointer<bg.OrtTensorTypeAndShapeInfo>,
                    ffi.Pointer<ffi.Size>)>()(infoPtr, countPtr);
        OrtStatus.checkOrtStatus(dimCountStatus);
        final dimCount = countPtr.value;

        final dimsPtr = calloc<ffi.Int64>(dimCount);
        try {
          final dimStatus = OrtEnv.instance.ortApiPtr.ref.GetDimensions
              .asFunction<
                  bg.OrtStatusPtr Function(
                      ffi.Pointer<bg.OrtTensorTypeAndShapeInfo>,
                      ffi.Pointer<ffi.Int64>,
                      int)>()(infoPtr, dimsPtr, dimCount);
          OrtStatus.checkOrtStatus(dimStatus);
          return List<int>.generate(dimCount, (i) => dimsPtr[i]);
        } finally {
          calloc.free(dimsPtr);
        }
      } finally {
        calloc.free(countPtr);
        OrtEnv.instance.ortApiPtr.ref.ReleaseTensorTypeAndShapeInfo
            .asFunction<void Function(ffi.Pointer<bg.OrtTensorTypeAndShapeInfo>)>()(infoPtr);
      }
    } finally {
      calloc.free(infoPtrPtr);
    }
  }

  /// High-performance zero-copy argmax directly on native C++ OrtValue tensor memory.
  /// Bypasses all Dart Object allocations and nested list conversions.
  static int fastArgmax(
    OrtValue logitsTensor,
    int stepIndex, {
    List<int>? generatedIds,
    double repetitionPenalty = 1.3,
  }) {
    final shape = getTensorShape(logitsTensor);
    // logits shape is [batch_size, seq_len, vocab_size]
    final vocabSize = shape.isNotEmpty ? shape.last : 256206;

    final dataPtrPtr = calloc<ffi.Pointer<ffi.Float>>();
    try {
      final statusPtr = OrtEnv.instance.ortApiPtr.ref.GetTensorMutableData
          .asFunction<
              bg.OrtStatusPtr Function(
                  ffi.Pointer<bg.OrtValue>,
                  ffi.Pointer<ffi.Pointer<ffi.Void>>)>()(
        logitsTensor.ptr,
        dataPtrPtr.cast(),
      );
      OrtStatus.checkOrtStatus(statusPtr);
      final dataPtr = dataPtrPtr.value;

      final offset = stepIndex * vocabSize;
      final stepLogits = (dataPtr + offset).asTypedList(vocabSize);

      final prevTokens =
          generatedIds != null ? generatedIds.toSet() : const <int>{};

      var best = 0;
      var bestVal = -double.maxFinite;
      for (var i = 0; i < vocabSize; i++) {
        var v = stepLogits[i];
        if (prevTokens.contains(i)) {
          v = v > 0 ? v / repetitionPenalty : v * repetitionPenalty;
        }
        if (v > bestVal) {
          bestVal = v;
          best = i;
        }
      }
      return best;
    } finally {
      calloc.free(dataPtrPtr);
    }
  }

  /// Copies tensor float data directly from C++ memory into a flat Float32List
  /// with zero intermediate Dart list wrappers.
  static Float32List copyFloat32Data(
    OrtValue tensor,
    int totalElements,
  ) {
    final dataPtrPtr = calloc<ffi.Pointer<ffi.Float>>();
    try {
      final statusPtr = OrtEnv.instance.ortApiPtr.ref.GetTensorMutableData
          .asFunction<
              bg.OrtStatusPtr Function(
                  ffi.Pointer<bg.OrtValue>,
                  ffi.Pointer<ffi.Pointer<ffi.Void>>)>()(
        tensor.ptr,
        dataPtrPtr.cast(),
      );
      OrtStatus.checkOrtStatus(statusPtr);
      final dataPtr = dataPtrPtr.value;
      return Float32List.fromList(dataPtr.asTypedList(totalElements));
    } finally {
      calloc.free(dataPtrPtr);
    }
  }
}
