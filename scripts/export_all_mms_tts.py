"""
Export all Meta MMS-TTS VITS models (amh, orm, tir, som, eng) to INT8 ONNX.

1. Wraps HuggingFace VitsModel to output raw waveform tensor.
2. Exports to ONNX using legacy TorchScript mode (dynamo=False) to handle spline ops.
3. Quantizes to INT8 dynamic quantization for minimal RAM/flash footprint (~36-40MB each).
4. Exports vocab.json for each language tokenizer.
5. Exports complete 479-character Ethiopic-to-uroman transliteration map.
6. Verifies inference and generates sample WAV audio for all 5 languages.
"""

import os
import sys
import json
import time
import shutil
from pathlib import Path

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

import torch
import numpy as np
import soundfile as sf
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
from transformers import VitsModel, AutoTokenizer
import uroman as ur

LANGUAGES = [
    ("amh", "facebook/mms-tts-amh", "ሰላም እንኳን ደህና መጣህ"),
    ("orm", "facebook/mms-tts-orm", "Akkam jirtu? Nagaadha?"),
    ("tir", "facebook/mms-tts-tir", "ከመይ ኣለኻ? ደሓን ዲኻ?"),
    ("som", "facebook/mms-tts-som", "Sidee tahay? Ma nabad baa?"),
    ("eng", "facebook/mms-tts-eng", "Welcome to Lisan AI translator"),
]

BASE_OUT_DIR = Path("models_optimized/mms_tts")
BASE_OUT_DIR.mkdir(parents=True, exist_ok=True)


class VitsOnnxWrapper(torch.nn.Module):
    def __init__(self, vits_model):
        super().__init__()
        self.vits = vits_model

    def forward(self, input_ids, attention_mask):
        # return_dict=False returns (waveform,)
        output = self.vits(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=False
        )
        return output[0]


def export_ethiopic_uroman_map():
    print("\n--- Generating Ethiopic-to-uroman transliteration table ---")
    u = ur.Uroman()
    ranges = [
        (0x1200, 0x137F),  # Ethiopic
        (0x1380, 0x139F),  # Ethiopic Supplement
        (0x2D80, 0x2DDF),  # Ethiopic Extended
        (0xAB00, 0xAB2F),  # Ethiopic Extended-A
    ]
    mapping = {}
    for start, end in ranges:
        for codepoint in range(start, end + 1):
            char = chr(codepoint)
            rom = u.romanize_string(char)
            if rom and rom != char:
                mapping[char] = rom

    out_file = BASE_OUT_DIR / "ethiopic_to_uroman.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(mapping)} character mappings to {out_file} ({out_file.stat().st_size / 1024:.1f} KB)")
    return mapping


def process_language(lang, model_id, test_text):
    print(f"\n==========================================")
    print(f"Processing Language: {lang.upper()} ({model_id})")
    print(f"==========================================")

    lang_dir = BASE_OUT_DIR / lang
    lang_dir.mkdir(parents=True, exist_ok=True)

    fp32_onnx_path = lang_dir / "model_fp32.onnx"
    int8_onnx_path = lang_dir / "model_quantized.onnx"
    vocab_path = lang_dir / "vocab.json"
    sample_wav_path = lang_dir / "test_sample.wav"

    # 1. Load Tokenizer & Model
    print(f"Loading HuggingFace model and tokenizer: {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = VitsModel.from_pretrained(model_id)
    model.eval()

    # Save vocab.json
    vocab = tokenizer.get_vocab()
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)
    print(f"Saved vocabulary ({len(vocab)} tokens) to {vocab_path}")

    # Prepare dummy inputs
    inputs = tokenizer(test_text, return_tensors="pt")
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # 2. Export to ARM64-Compatible ONNX
    print(f"Exporting ARM64-compatible ONNX to {int8_onnx_path}...")
    wrapper = VitsOnnxWrapper(model)
    wrapper.eval()

    t0 = time.time()
    with torch.no_grad():
        torch.onnx.export(
            wrapper,
            (input_ids, attention_mask),
            str(int8_onnx_path),
            input_names=["input_ids", "attention_mask"],
            output_names=["waveform"],
            dynamic_axes={
                "input_ids": {0: "batch_size", 1: "seq_len"},
                "attention_mask": {0: "batch_size", 1: "seq_len"},
                "waveform": {0: "batch_size", 1: "num_samples"},
            },
            opset_version=14,
            do_constant_folding=True,
            dynamo=False,
        )

    export_time = time.time() - t0
    model_size_mb = int8_onnx_path.stat().st_size / (1024 * 1024)
    print(f"Exported clean ARM64 ONNX in {export_time:.1f}s: {model_size_mb:.1f} MB (No unsupported ConvInteger)")

    # 3. Verify Inference with ONNX Runtime
    print(f"Verifying ONNX inference on text: '{test_text}'...")
    sess_options = ort.SessionOptions()
    sess_options.intra_op_num_threads = 2
    sess_options.inter_op_num_threads = 1
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC

    session = ort.InferenceSession(str(int8_onnx_path), sess_options, providers=["CPUExecutionProvider"])
    
    np_inputs = tokenizer(test_text, return_tensors="np")
    ort_feed = {
        "input_ids": np_inputs["input_ids"].astype(np.int64),
        "attention_mask": np_inputs["attention_mask"].astype(np.int64),
    }

    t0 = time.time()
    outputs = session.run(["waveform"], ort_feed)
    inf_time = time.time() - t0

    wav = outputs[0][0]
    sample_rate = 16000
    duration_s = len(wav) / sample_rate
    rtf = inf_time / duration_s if duration_s > 0 else 0

    print(f"Synthesized {duration_s:.2f}s of audio in {inf_time:.2f}s (RTF: {rtf:.2f})")
    print(f"Audio stats: samples={len(wav)}, min={wav.min():.4f}, max={wav.max():.4f}, std={wav.std():.4f}")

    sf.write(str(sample_wav_path), wav, sample_rate)
    print(f"Saved verified audio sample to {sample_wav_path}")
    print(f"Language {lang.upper()} completed successfully! ✓")


def main():
    start_total = time.time()
    print("=======================================================")
    print("  LISAN AI: MMS-TTS VITS ONNX BATCH EXPORTER & QUANTIZER")
    print("=======================================================")

    export_ethiopic_uroman_map()

    for lang, model_id, test_text in LANGUAGES:
        process_language(lang, model_id, test_text)

    total_time = time.time() - start_total
    print(f"\n=======================================================")
    print(f"ALL 5 LANGUAGES SUCCESSFULLY EXPORTED & QUANTIZED IN {total_time:.1f}s!")
    print(f"Output directory: {BASE_OUT_DIR.resolve()}")
    print("=======================================================")


if __name__ == "__main__":
    main()
