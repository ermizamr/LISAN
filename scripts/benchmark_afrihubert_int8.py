import sys
import os
import time
import ctypes
from ctypes import wintypes
import soundfile as sf
import numpy as np
import onnxruntime as ort
from transformers import AutoProcessor

sys.stdout.reconfigure(encoding='utf-8')

class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ('cb', wintypes.DWORD),
        ('PageFaultCount', wintypes.DWORD),
        ('PeakWorkingSetSize', ctypes.c_size_t),
        ('WorkingSetSize', ctypes.c_size_t),
        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPagedPoolUsage', ctypes.c_size_t),
        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
        ('PagefileUsage', ctypes.c_size_t),
        ('PeakPagefileUsage', ctypes.c_size_t),
    ]

def get_ram_mb():
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
    return counters.WorkingSetSize / (1024 * 1024)

def benchmark():
    model_path = "onnx_models/afrihubert/int8/model_quantized.onnx"
    vocab_dir = "onnx_models/afrihubert/int8"
    test_audio = "ai_pipeline/test_audio/test_amh.wav"

    ram_before = get_ram_mb()

    print(f"Loading ONNX model: {model_path} ({os.path.getsize(model_path)/(1024*1024):.1f} MB)...")
    sess_options = ort.SessionOptions()
    sess_options.intra_op_num_threads = 2
    sess_options.inter_op_num_threads = 1
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC

    t0 = time.time()
    session = ort.InferenceSession(model_path, sess_options, providers=['CPUExecutionProvider'])
    load_time = time.time() - t0

    ram_after_load = get_ram_mb()
    ram_delta_load = ram_after_load - ram_before
    print(f"Model loaded in {load_time:.2f}s | RAM Delta: {ram_delta_load:.1f} MB (Current RSS: {ram_after_load:.1f} MB)")

    processor = AutoProcessor.from_pretrained(vocab_dir, local_files_only=True)
    wav, sr = sf.read(test_audio)
    if sr != 16000:
        import librosa
        wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)

    # Normalize audio for model
    input_values = processor(wav, sampling_rate=16000, return_tensors="np").input_values.astype(np.float32)

    print(f"Running inference on {len(wav)/16000:.2f}s audio (shape {input_values.shape})...")
    t1 = time.time()
    outputs = session.run(["logits"], {"input_values": input_values})
    infer_time = time.time() - t1

    logits = outputs[0]
    pred_ids = np.argmax(logits, axis=-1)[0]
    decoded_text = processor.decode(pred_ids)

    ram_peak = get_ram_mb()
    ram_delta_total = ram_peak - ram_before

    print("\n========== BENCHMARK RESULTS ==========")
    print(f"Decoded Text    : {decoded_text}")
    print(f"Inference Latency: {infer_time:.2f}s")
    print(f"Model Load RAM   : +{ram_delta_load:.1f} MB")
    print(f"Peak Working RAM : +{ram_delta_total:.1f} MB")
    print(f"Gate 2 Verdict   : {'PASS (<= 80 MB working RAM)' if ram_delta_total <= 80 else 'FAIL'}")
    print("========================================")

if __name__ == "__main__":
    benchmark()
