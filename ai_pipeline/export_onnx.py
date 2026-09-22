"""
Export Ethiopian Translator models to ONNX INT8
================================================
Run this ONCE on your PC to produce quantized models for Android.

Output layout (copy to Android assets/):
  onnx_models/
    nllb/
      encoder_model.onnx         (~150MB INT8)
      decoder_model_merged.onnx  (~300MB INT8)
      tokenizer files
    ethio_stt/
      model.onnx                 (~150MB INT8)
      tokenizer files

Usage:
  python ai_pipeline/export_onnx.py

Requires:
  pip install optimum[onnxruntime] onnxruntime
"""

import os
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()
OUTPUT_DIR = Path(__file__).parent.parent / "onnx_models"


def export_nllb():
    """Export NLLB-200-distilled-600M to ONNX INT8."""
    from optimum.onnxruntime import ORTModelForSeq2SeqLM
    from transformers import AutoTokenizer
    from optimum.onnxruntime.configuration import AutoQuantizationConfig
    from optimum.onnxruntime import ORTQuantizer

    out = OUTPUT_DIR / "nllb"
    out.mkdir(parents=True, exist_ok=True)

    console.print(Panel("[cyan]Exporting NLLB-200 → ONNX float32...[/cyan]"))
    t0 = time.time()

    model_id = "facebook/nllb-200-distilled-600M"

    # Export to ONNX (float32 first)
    console.print("  Step 1/2: Export to ONNX...")
    model = ORTModelForSeq2SeqLM.from_pretrained(model_id, export=True)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model.save_pretrained(str(out))
    tokenizer.save_pretrained(str(out))

    console.print(f"  Exported in {time.time()-t0:.0f}s")
    console.print("  Step 2/2: Quantizing to INT8...")
    t1 = time.time()

    # Dynamic INT8 quantization (works on CPU, good for transformer encoders)
    qconfig = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=False)
    
    for onnx_file in out.glob("*.onnx"):
        quantizer = ORTQuantizer.from_pretrained(str(out), file_name=onnx_file.name)
        quantizer.quantize(
            save_dir=str(out / "int8"),
            quantization_config=qconfig,
        )
        console.print(f"    Quantized: {onnx_file.name}")

    total = time.time() - t0
    console.print(f"[green]✓ NLLB ONNX INT8 done in {total:.0f}s → {out}/int8[/green]")
    _print_sizes(out / "int8")


def export_ethio_stt():
    """Export EthioMultilingualSTT to ONNX INT8."""
    from optimum.onnxruntime import ORTModelForCTC
    from transformers import AutoProcessor
    from optimum.onnxruntime.configuration import AutoQuantizationConfig
    from optimum.onnxruntime import ORTQuantizer

    out = OUTPUT_DIR / "ethio_stt"
    out.mkdir(parents=True, exist_ok=True)

    console.print(Panel("[cyan]Exporting EthioMultilingualSTT → ONNX float32...[/cyan]"))
    t0 = time.time()

    model_id = "badrex/Ethio-ASR-multilingual-600M"

    # Export to ONNX
    console.print("  Step 1/2: Export to ONNX...")
    model = ORTModelForCTC.from_pretrained(model_id, export=True)
    processor = AutoProcessor.from_pretrained(model_id)
    model.save_pretrained(str(out))
    processor.save_pretrained(str(out))

    console.print(f"  Exported in {time.time()-t0:.0f}s")
    console.print("  Step 2/2: Quantizing to INT8...")
    t1 = time.time()

    qconfig = AutoQuantizationConfig.avx512_vnni(is_static=False, per_channel=False)
    for onnx_file in out.glob("*.onnx"):
        quantizer = ORTQuantizer.from_pretrained(str(out), file_name=onnx_file.name)
        quantizer.quantize(
            save_dir=str(out / "int8"),
            quantization_config=qconfig,
        )
        console.print(f"    Quantized: {onnx_file.name}")

    total = time.time() - t0
    console.print(f"[green]✓ EthioSTT ONNX INT8 done in {total:.0f}s → {out}/int8[/green]")
    _print_sizes(out / "int8")


def _print_sizes(directory: Path):
    """Print file sizes in a directory."""
    if not directory.exists():
        return
    total = 0
    for f in sorted(directory.glob("*")):
        if f.is_file():
            mb = f.stat().st_size / 1e6
            total += mb
            console.print(f"    {f.name:<45} {mb:6.1f} MB")
    console.print(f"    {'TOTAL':<45} {total:6.1f} MB")


def verify_nllb_onnx():
    """Quick smoke test: run a translation with the ONNX model."""
    from optimum.onnxruntime import ORTModelForSeq2SeqLM
    from transformers import AutoTokenizer

    int8_dir = OUTPUT_DIR / "nllb" / "int8"
    if not int8_dir.exists():
        console.print("[yellow]NLLB INT8 not found, run export first[/yellow]")
        return

    console.print("[cyan]Testing NLLB ONNX inference...[/cyan]")
    model = ORTModelForSeq2SeqLM.from_pretrained(str(int8_dir))
    tokenizer = AutoTokenizer.from_pretrained(str(OUTPUT_DIR / "nllb"))

    tokenizer.src_lang = "eng_Latn"
    inputs = tokenizer("Where is the hospital?", return_tensors="pt")
    tgt_id = tokenizer.convert_tokens_to_ids("amh_Ethi")

    import time
    t = time.time()
    outputs = model.generate(**inputs, forced_bos_token_id=tgt_id, max_length=128, num_beams=2)
    result = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]
    console.print(f"[green]ONNX result ({time.time()-t:.2f}s): {result}[/green]")


if __name__ == "__main__":
    console.print(Panel(
        "[bold yellow]Ethiopian Translator — ONNX Export[/bold yellow]\n"
        "[dim]Produces INT8 quantized models for Android on-device inference[/dim]",
        expand=False
    ))

    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    if mode in ("all", "nllb"):
        export_nllb()

    if mode in ("all", "stt"):
        export_ethio_stt()

    if mode == "verify":
        verify_nllb_onnx()

    console.print(Panel(
        "[bold green]Export complete![/bold green]\n"
        f"[dim]Models saved to: {OUTPUT_DIR}[/dim]\n"
        "[dim]Copy onnx_models/ folder to your Android project assets/[/dim]"
    ))
