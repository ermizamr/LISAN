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


def _cached_snapshot(repo_id: str) -> tuple[str, bool]:
    """Return a local Hugging Face snapshot when one is available."""
    import os

    repo_dir = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub" / f"models--{repo_id.replace('/', '--')}" / "snapshots"
    snapshots = sorted(repo_dir.glob("*"), key=lambda path: path.stat().st_mtime, reverse=True)
    for snapshot in snapshots:
        if snapshot.is_dir() and (snapshot / "config.json").exists():
            return str(snapshot), True
    return repo_id, False


def _ethio_ctc_onnx_config(model_id: str):
    """Build the custom Optimum schema required by Wav2Vec2Bert CTC models."""
    from transformers import AutoConfig
    from optimum.exporters.onnx import OnnxConfig
    from optimum.utils.normalized_config import NormalizedConfig

    class EthioCTCOnnxConfig(OnnxConfig):
        NORMALIZED_CONFIG_CLASS = NormalizedConfig

        @property
        def inputs(self):
            return {"input_features": {0: "batch_size", 1: "audio_sequence_length", 2: "feature_size"}}

        def generate_dummy_inputs(self, framework="pt", **_kwargs):
            if framework != "pt":
                raise ValueError("Ethio-ASR export supports the PyTorch source framework only")
            import torch

            return {"input_features": torch.zeros((1, 100, 160), dtype=torch.float32)}

    config = AutoConfig.from_pretrained(model_id, local_files_only=True)
    return EthioCTCOnnxConfig(config, task="automatic-speech-recognition")


def export_nllb(model_path: str | None = None):
    """Export NLLB-200 (base or custom fine-tuned) to ONNX INT8."""
    from optimum.onnxruntime import ORTModelForSeq2SeqLM
    from transformers import AutoTokenizer
    from optimum.onnxruntime.configuration import AutoQuantizationConfig
    from optimum.onnxruntime import ORTQuantizer

    out = OUTPUT_DIR / "nllb"
    out.mkdir(parents=True, exist_ok=True)

    console.print(Panel("[cyan]Exporting NLLB-200 → ONNX float32...[/cyan]"))
    t0 = time.time()

    merged_candidate = OUTPUT_DIR.parent / "models_optimized" / "nllb_merged"
    ethio_candidate = OUTPUT_DIR.parent / "models_optimized" / "nllb_ethio_finetuned"

    if model_path and Path(model_path).exists():
        model_id = str(model_path)
        local_files_only = True
        console.print(f"[green]  Using specified fine-tuned model: {model_id}[/green]")
    elif merged_candidate.exists() and (merged_candidate / "config.json").exists():
        model_id = str(merged_candidate)
        local_files_only = True
        console.print(f"[green]  Found fine-tuned merged model: {model_id}[/green]")
    elif ethio_candidate.exists() and (ethio_candidate / "config.json").exists():
        model_id = str(ethio_candidate)
        local_files_only = True
        console.print(f"[green]  Found fine-tuned model: {model_id}[/green]")
    else:
        model_id, local_files_only = _cached_snapshot("facebook/nllb-200-distilled-600M")
        console.print(f"[cyan]  Using base model snapshot: {model_id}[/cyan]")

    # Export to ONNX (float32 first)
    console.print("  Step 1/2: Export to ONNX...")
    model = ORTModelForSeq2SeqLM.from_pretrained(model_id, export=True, local_files_only=local_files_only)
    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=local_files_only)
    model.save_pretrained(str(out))
    tokenizer.save_pretrained(str(out))

    console.print(f"  Exported in {time.time()-t0:.0f}s")
    console.print("  Step 2/2: Quantizing to INT8...")
    t1 = time.time()

    # Dynamic INT8 quantization (works on CPU, good for transformer encoders)
    qconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=False)
    
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
    from optimum.exporters.onnx import main_export
    from transformers import AutoProcessor
    from optimum.onnxruntime.configuration import AutoQuantizationConfig
    from optimum.onnxruntime import ORTQuantizer

    out = OUTPUT_DIR / "ethio_stt"
    out.mkdir(parents=True, exist_ok=True)

    console.print(Panel("[cyan]Exporting EthioMultilingualSTT → ONNX float32...[/cyan]"))
    t0 = time.time()

    model_id, local_files_only = _cached_snapshot("badrex/Ethio-ASR-multilingual-600M")

    # Export to ONNX
    console.print("  Step 1/2: Export to ONNX...")
    custom_config = _ethio_ctc_onnx_config(model_id)
    main_export(
        model_id,
        output=out,
        task="automatic-speech-recognition",
        local_files_only=local_files_only,
        custom_onnx_configs={"model": custom_config},
    )
    processor = AutoProcessor.from_pretrained(model_id, local_files_only=local_files_only)
    processor.save_pretrained(str(out))

    console.print(f"  Exported in {time.time()-t0:.0f}s")
    console.print("  Step 2/2: Quantizing to INT8...")
    t1 = time.time()

    qconfig = AutoQuantizationConfig.arm64(is_static=False, per_channel=False)
    # Exclude Conv from quantization to prevent unsupported ConvInteger nodes on Android mobile CPU
    qconfig.operators_to_quantize = [op for op in qconfig.operators_to_quantize if op != "Conv"]
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
    import argparse
    parser = argparse.ArgumentParser(description="Export Ethiopian Translator models to ONNX INT8")
    parser.add_argument("mode", nargs="?", default="all", choices=["all", "nllb", "stt", "verify"],
                        help="Export mode (default: all)")
    parser.add_argument("--model_path", type=str, default=None,
                        help="Optional path to custom fine-tuned NLLB checkpoint directory")
    args = parser.parse_args()

    console.print(Panel(
        "[bold yellow]Ethiopian Translator — ONNX Export[/bold yellow]\n"
        "[dim]Produces INT8 quantized models for Android on-device inference[/dim]",
        expand=False
    ))

    if args.mode in ("all", "nllb"):
        export_nllb(model_path=args.model_path)

    if args.mode in ("all", "stt"):
        export_ethio_stt()

    if args.mode == "verify":
        verify_nllb_onnx()

    console.print(Panel(
        "[bold green]Export complete![/bold green]\n"
        f"[dim]Models saved to: {OUTPUT_DIR}[/dim]\n"
        "[dim]Copy onnx_models/ folder to your Android project assets/[/dim]"
    ))
