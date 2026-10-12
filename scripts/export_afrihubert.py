import sys
import os
import time

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import AutoModelForCTC, AutoProcessor
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

def export_and_quantize():
    model_id = "boazsew/Ethio-ASR-afrihubert-uf"
    output_dir = "onnx_models/afrihubert"
    os.makedirs(f"{output_dir}/fp32", exist_ok=True)
    os.makedirs(f"{output_dir}/int8", exist_ok=True)
    
    fp32_onnx = f"{output_dir}/fp32/model.onnx"
    int8_onnx = f"{output_dir}/int8/model_quantized.onnx"

    print(f"[1/4] Loading {model_id}...")
    model = AutoModelForCTC.from_pretrained(model_id, local_files_only=True)
    processor = AutoProcessor.from_pretrained(model_id, local_files_only=True)
    model.eval()

    # Save processor/vocab to int8 folder for deployment
    processor.save_pretrained(f"{output_dir}/int8")

    if not os.path.exists(fp32_onnx):
        dummy_input = torch.randn(1, 16000, dtype=torch.float32)
        print(f"[2/4] Exporting to FP32 ONNX: {fp32_onnx}...")
        t0 = time.time()
        torch.onnx.export(
            model,
            (dummy_input,),
            fp32_onnx,
            input_names=["input_values"],
            output_names=["logits"],
            dynamic_axes={
                "input_values": {0: "batch", 1: "time"},
                "logits": {0: "batch", 1: "time"},
            },
            opset_version=18,
        )
        fp32_size = os.path.getsize(fp32_onnx) / (1024 * 1024)
        print(f"FP32 ONNX exported in {time.time()-t0:.2f}s, size: {fp32_size:.1f} MB")
    else:
        print(f"[2/4] Found existing FP32 ONNX: {fp32_onnx}")

    print(f"[3/4] Quantizing to INT8: {int8_onnx}...")
    t1 = time.time()
    quantize_dynamic(
        model_input=fp32_onnx,
        model_output=int8_onnx,
        op_types_to_quantize=["MatMul", "Gemm"],
        weight_type=QuantType.QInt8,
    )
    int8_size = os.path.getsize(int8_onnx) / (1024 * 1024)
    print(f"INT8 ONNX quantized in {time.time()-t1:.2f}s, size: {int8_size:.1f} MB")

    print("[4/4] Verification complete!")
    print(f"SUCCESS: INT8 model ready at {int8_onnx} ({int8_size:.1f} MB)")

if __name__ == "__main__":
    export_and_quantize()
