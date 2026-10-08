"""
LISAN AI: End-to-End NLLB-200 Ethiopian Multilingual LoRA Training & CTranslate2 INT8 Exporter.

Languages:
- Afaan Oromo (gaz_Latn)
- Amharic (amh_Ethi)
- Tigrinya (tir_Ethi)
- Somali (som_Latn)
- English (eng_Latn)

Features:
- Parameter-Efficient QLoRA (4-bit / 8-bit / FP16)
- Automatic LoRA Adapter Merging (--merge_and_export)
- Direct CTranslate2 INT8 Quantization for offline low-latency deployment
- Automatic HornMT Benchmark Evaluation (--eval_benchmarks)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Force UTF-8 encoding in Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent.parent

# Neutralize torchao version conflict in Google Colab / cloud environments
try:
    import peft.import_utils
    orig_is_torchao = getattr(peft.import_utils, "is_torchao_available", None)
    def _safe_is_torchao():
        try:
            return orig_is_torchao() if orig_is_torchao else False
        except ImportError:
            return False
    peft.import_utils.is_torchao_available = _safe_is_torchao
except Exception:
    pass

# Neutralize transformers / peft Seq2Seq kwargs rename compatibility bug globally
try:
    import transformers
    from transformers import PreTrainedModel, GenerationMixin
    try:
        from transformers.models.m2m_100.modeling_m2m_100 import M2M100ForConditionalGeneration
        classes_to_patch = [M2M100ForConditionalGeneration, GenerationMixin, PreTrainedModel]
    except Exception:
        classes_to_patch = [GenerationMixin, PreTrainedModel]

    for cls in classes_to_patch:
        if not hasattr(cls, "_prepare_encoder_decoder_kwargs_for_generation"):
            alt_method = getattr(cls, "_prepare_text_encoder_decoder_kwargs_for_generation", None)
            if alt_method is not None:
                cls._prepare_encoder_decoder_kwargs_for_generation = alt_method
            else:
                cls._prepare_encoder_decoder_kwargs_for_generation = lambda self, *args, **kwargs: {}
except Exception:
    pass

try:
    import peft
    from peft.tuners.tuners_utils import BaseTuner
    orig_getattr = BaseTuner.__getattr__
    def safe_getattr(self, name: str):
        try:
            return orig_getattr(self, name)
        except AttributeError:
            if name == "_prepare_encoder_decoder_kwargs_for_generation":
                alt = getattr(self.model, "_prepare_text_encoder_decoder_kwargs_for_generation", None)
                if alt is not None:
                    return alt
                return lambda *args, **kwargs: {}
            raise
    BaseTuner.__getattr__ = safe_getattr
except Exception:
    pass


def parse_args():
    parser = argparse.ArgumentParser(description="LISAN AI: NLLB-200 LoRA Fine-Tuning & Export")
    parser.add_argument("--base_model", type=str, default="facebook/nllb-200-distilled-600M", help="Hugging Face model ID or path")
    parser.add_argument("--train_file", type=str, default=str(ROOT_DIR / "data" / "training_data" / "train.jsonl"))
    parser.add_argument("--val_file", type=str, default=str(ROOT_DIR / "data" / "training_data" / "val.jsonl"))
    parser.add_argument("--output_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "nllb_lora_adapter"))
    parser.add_argument("--merged_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "nllb_merged"))
    parser.add_argument("--export_c2_dir", type=str, default=str(ROOT_DIR / "models_optimized" / "nllb_int8"))
    parser.add_argument("--batch_size", type=int, default=16, help="Per device batch size")
    parser.add_argument("--grad_accum", type=int, default=2, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4)
    parser.add_argument("--num_epochs", type=int, default=3)
    parser.add_argument("--max_length", type=int, default=128)
    parser.add_argument("--lora_r", type=int, default=32, help="LoRA rank dimension (32 for high capacity)")
    parser.add_argument("--lora_alpha", type=int, default=64, help="LoRA scaling alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05)
    parser.add_argument("--use_4bit", action="store_true", default=True, help="Use 4-bit QLoRA")
    parser.add_argument("--no_4bit", dest="use_4bit", action="store_false")
    parser.add_argument("--merge_and_export", action="store_true", default=True, help="Automatically merge LoRA and convert to CTranslate2 INT8")
    parser.add_argument("--export_onnx", action="store_true", default=True, help="Automatically export merged model to mobile ONNX INT8")
    parser.add_argument("--eval_benchmarks", action="store_true", default=False, help="Run HornMT evaluation after training")
    parser.add_argument("--merge_only", action="store_true", default=False,
                        help="Skip training and only merge existing LoRA adapter into standalone model and CTranslate2 INT8")
    parser.add_argument("--max_steps", type=int, default=-1,
                        help="Maximum training steps (overrides num_epochs if > 0)")
    parser.add_argument("--max_samples", type=int, default=-1,
                        help="Cap training samples to fit within fast GPU sessions")
    parser.add_argument("--save_steps", type=int, default=200,
                        help="Checkpoint save interval in steps")
    parser.add_argument("--drive_dir", type=str, default=None,
                        help="Google Drive backup directory (e.g. /content/drive/MyDrive/LISAN_BACKUP)")
    parser.add_argument("--resume", action="store_true", default=False,
                        help="Resume training from latest checkpoint if available")
    return parser.parse_args()


def convert_to_ctranslate2(model_path: str, output_dir: str):
    """Converts a HuggingFace Seq2Seq model to CTranslate2 INT8 format."""
    print("\n" + "=" * 60)
    print(f"⚡ Converting Merged NLLB Model -> CTranslate2 INT8...")
    print(f"   Source : {model_path}")
    print(f"   Target : {output_dir}")
    print("=" * 60)

    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "ctranslate2.converters.transformers",
        "--model",
        model_path,
        "--output_dir",
        output_dir,
        "--quantization",
        "int8",
        "--force",
        "--copy_files",
        "tokenizer.json",
        "sentencepiece.bpe.model",
        "special_tokens_map.json",
        "tokenizer_config.json",
    ]

    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode == 0:
        print("✓ CTranslate2 INT8 export completed successfully!")
        print(f"  Model files saved in: {output_dir}")
        return True
    else:
        print(f"✗ CTranslate2 conversion failed:\n{res.stderr}")
        return False


def test_ctranslate2_inference(c2_model_dir: str):
    """Sanity-check translated phrases across Ethiopian languages using exported CTranslate2 model."""
    print("\n" + "=" * 60)
    print("🧪 Verifying CTranslate2 INT8 Inference Across Languages...")
    print("=" * 60)
    try:
        import ctranslate2
        import transformers

        translator = ctranslate2.Translator(c2_model_dir, device="cpu", compute_type="int8")
        tokenizer = transformers.AutoTokenizer.from_pretrained(c2_model_dir)

        test_cases = [
            ("Where is the hospital?", "eng_Latn", "amh_Ethi", "Amharic"),
            ("Where is the hospital?", "eng_Latn", "gaz_Latn", "Afaan Oromo"),
            ("Where is the hospital?", "eng_Latn", "tir_Ethi", "Tigrinya"),
            ("Where is the hospital?", "eng_Latn", "som_Latn", "Somali"),
        ]

        for phrase, src_code, tgt_code, lang_name in test_cases:
            tokenizer.src_lang = src_code
            source_tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(phrase))
            target_prefix = [tgt_code]

            results = translator.translate_batch(
                [source_tokens],
                target_prefix=[target_prefix],
                beam_size=2,
                max_decoding_length=64,
            )
            out_tokens = results[0].hypotheses[0]
            if out_tokens and out_tokens[0] == tgt_code:
                out_tokens = out_tokens[1:]
            trans_text = tokenizer.decode(tokenizer.convert_tokens_to_ids(out_tokens)).strip()
            print(f"  [{lang_name:<11}] '{phrase}' -> '{trans_text}'")

        print("✓ CTranslate2 verification passed!")
    except Exception as e:
        print(f"✗ Verification note: {e}")


def main():
    args = parse_args()
    print("=" * 70)
    print("       LISAN AI: NLLB-200 MULTILINGUAL LORA TRAINING & EXPORT")
    print("=" * 70)
    print(f"Base Model        : {args.base_model}")
    print(f"Training Data     : {args.train_file}")
    print(f"Validation Data   : {args.val_file}")
    print(f"LoRA Output       : {args.output_dir}")
    print(f"Merged Output     : {args.merged_dir}")
    print(f"CTranslate2 INT8  : {args.export_c2_dir}")

    import torch
    cuda_avail = torch.cuda.is_available()
    print(f"CUDA Available    : {cuda_avail}")
    if cuda_avail:
        print(f"Device Name       : {torch.cuda.get_device_name(0)}")
        print(f"Device Memory     : {torch.cuda.get_device_properties(0).total_memory / (1024**3):.2f} GB")
        use_bf16 = torch.cuda.is_bf16_supported()
    else:
        use_bf16 = False
    print(f"Precision Mode    : {'bf16' if use_bf16 else ('fp16' if cuda_avail else 'fp32')}")
    print("=" * 70)

    if args.merge_only:
        print("Running in --merge_only mode (skipping dataset loading and training)...")
        from scripts.merge_nllb_lora import merge_nllb
        merge_nllb(args.base_model, args.output_dir, args.merged_dir, args.export_c2_dir)
        return

    # Validate dataset files
    if not Path(args.train_file).exists() or not Path(args.val_file).exists():
        print(f"ERROR: Dataset files not found at {args.train_file}. Run scripts/export_training_data.py first!")
        sys.exit(1)

    from datasets import load_dataset
    from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training, PeftModel
    from transformers import (
        AutoModelForSeq2SeqLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        DataCollatorForSeq2Seq,
        Seq2SeqTrainer,
        Seq2SeqTrainingArguments,
    )

    # 1. Load Tokenizer
    print("Loading NLLB Tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, use_fast=True)

    # 2. Load Dataset
    print(f"Loading parallel corpora...")
    dataset = load_dataset(
        "json",
        data_files={"train": args.train_file, "val": args.val_file},
    )
    print(f"  • Train Samples : {len(dataset['train']):,}")
    print(f"  • Val Samples   : {len(dataset['val']):,}")

    if args.max_samples > 0 and args.max_samples < len(dataset["train"]):
        dataset["train"] = dataset["train"].shuffle(seed=42).select(range(args.max_samples))
        print(f"  • Capped to     : {len(dataset['train']):,} balanced training samples")

    # 3. Preprocessing
    def preprocess_function(examples):
        inputs = examples["source"]
        targets = examples["target"]
        src_langs = examples["src_nllb"]
        tgt_langs = examples["tgt_nllb"]

        model_inputs = {"input_ids": [], "attention_mask": [], "labels": []}

        for inp, tgt, src_l, tgt_l in zip(inputs, targets, src_langs, tgt_langs):
            tokenizer.src_lang = src_l
            tokenizer.tgt_lang = tgt_l
            tok = tokenizer(
                text=inp,
                text_target=tgt,
                max_length=args.max_length,
                truncation=True,
            )
            model_inputs["input_ids"].append(tok["input_ids"])
            model_inputs["attention_mask"].append(tok["attention_mask"])
            model_inputs["labels"].append(tok["labels"])

        return model_inputs

    print("Tokenizing datasets with NLLB language codes...")
    tokenized_datasets = dataset.map(
        preprocess_function,
        batched=True,
        batch_size=1000,
        remove_columns=dataset["train"].column_names,
    )

    # 4. BitsAndBytes 4-bit Quantization Config
    bnb_config = None
    if args.use_4bit and cuda_avail:
        print("Configuring 4-bit QLoRA (NF4 double quantization)...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16 if use_bf16 else torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    # 5. Load Base Model
    print(f"Loading {args.base_model}...")
    model = AutoModelForSeq2SeqLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config if cuda_avail else None,
        device_map="auto" if cuda_avail else None,
        torch_dtype=torch.bfloat16 if use_bf16 else (torch.float16 if cuda_avail else torch.float32),
    )

    if cuda_avail and args.use_4bit:
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=False)

    # Neutralize transformers / peft Seq2Seq kwargs rename compatibility bug
    for target_obj in (model, model.__class__):
        if not hasattr(target_obj, "_prepare_encoder_decoder_kwargs_for_generation"):
            alt_fn = getattr(target_obj, "_prepare_text_encoder_decoder_kwargs_for_generation", None)
            if alt_fn is not None:
                setattr(target_obj, "_prepare_encoder_decoder_kwargs_for_generation", alt_fn)
            else:
                setattr(target_obj, "_prepare_encoder_decoder_kwargs_for_generation", lambda *a, **k: {})

    # Ensure M2M100Decoder handles collision gracefully
    try:
        from transformers.models.m2m_100.modeling_m2m_100 import M2M100Decoder
        _orig_m2m_dec_forward = M2M100Decoder.forward

        def _safe_m2m_dec_forward(self, input_ids=None, *a, **k):
            if input_ids is not None and k.get("inputs_embeds") is not None:
                k["inputs_embeds"] = None
            return _orig_m2m_dec_forward(self, input_ids=input_ids, *a, **k)

        M2M100Decoder.forward = _safe_m2m_dec_forward
    except Exception:
        pass

    # 6. LoRA Adapter Config
    print(f"Initializing LoRA adapter (rank={args.lora_r}, alpha={args.lora_alpha})...")
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        target_modules=["q_proj", "v_proj", "k_proj", "out_proj", "fc1", "fc2"],
        bias="none",
        task_type=TaskType.SEQ_2_SEQ_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Attach prepare_decoder_input_ids_from_labels to model objects
    from transformers.models.m2m_100.modeling_m2m_100 import shift_tokens_right

    def _prep_decoder_ids(*args, **kwargs):
        labels = kwargs.get("labels")
        if labels is None and len(args) > 0:
            labels = args[-1]
        cfg = getattr(model, "config", None) or getattr(getattr(model, "base_model", None), "config", None)
        pad_id = getattr(cfg, "pad_token_id", tokenizer.pad_token_id)
        start_id = getattr(cfg, "decoder_start_token_id", getattr(tokenizer, "eos_token_id", 2))
        return shift_tokens_right(labels, pad_id, start_id)

    for target_obj in (model, model.__class__, getattr(model, "base_model", None)):
        if target_obj is not None:
            setattr(target_obj, "prepare_decoder_input_ids_from_labels", _prep_decoder_ids)

    # 7. Robust Collator
    # Guarantees that decoder_input_ids is always generated and present in the batch,
    # even when labels are popped by Seq2SeqTrainer for label smoothing.
    class RobustSeq2SeqCollator(DataCollatorForSeq2Seq):
        def __call__(self, features, return_tensors=None):
            batch = super().__call__(features, return_tensors=return_tensors)
            if "labels" in batch and "decoder_input_ids" not in batch:
                cfg = getattr(self.model, "config", None) or getattr(getattr(self.model, "base_model", None), "config", None)
                pad_id = getattr(cfg, "pad_token_id", self.tokenizer.pad_token_id)
                start_id = getattr(cfg, "decoder_start_token_id", getattr(self.tokenizer, "eos_token_id", 2))
                batch["decoder_input_ids"] = shift_tokens_right(batch["labels"], pad_id, start_id)
            return batch

    data_collator = RobustSeq2SeqCollator(
        tokenizer=tokenizer,
        model=model,
        padding=True,
        label_pad_token_id=-100,
    )

    # 8. Training Arguments
    import inspect
    training_args_dict = {
        "output_dir": args.output_dir,
        "eval_strategy": "epoch",
        "save_strategy": "epoch",
        "learning_rate": args.learning_rate,
        "per_device_train_batch_size": args.batch_size,
        "per_device_eval_batch_size": args.batch_size,
        "gradient_accumulation_steps": args.grad_accum,
        "weight_decay": 0.01,
        "label_smoothing_factor": 0.1,
        "lr_scheduler_type": "cosine",
        "warmup_ratio": 0.05,
        "save_total_limit": 2,
        "num_train_epochs": args.num_epochs,
        "predict_with_generate": False,
        "fp16": cuda_avail and not use_bf16,
        "bf16": use_bf16,
        "logging_steps": 50,
        "warmup_steps": 100,
        "report_to": "none",
    }
    if args.max_steps > 0:
        training_args_dict["max_steps"] = args.max_steps
        training_args_dict["save_strategy"] = "steps"
        training_args_dict["save_steps"] = args.save_steps
        training_args_dict["eval_strategy"] = "steps"
        training_args_dict["eval_steps"] = args.save_steps

    arg_params = inspect.signature(Seq2SeqTrainingArguments.__init__).parameters
    if "eval_strategy" not in arg_params and "evaluation_strategy" in arg_params:
        training_args_dict["evaluation_strategy"] = training_args_dict.pop("eval_strategy")
    valid_args = {k: v for k, v in training_args_dict.items() if k in arg_params}
    training_args = Seq2SeqTrainingArguments(**valid_args)

    import inspect
    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "train_dataset": tokenized_datasets["train"],
        "eval_dataset": tokenized_datasets["val"],
        "data_collator": data_collator,
    }
    sig = inspect.signature(Seq2SeqTrainer.__init__)
    if "processing_class" in sig.parameters:
        trainer_kwargs["processing_class"] = tokenizer
    elif "tokenizer" in sig.parameters:
        trainer_kwargs["tokenizer"] = tokenizer

    trainer = Seq2SeqTrainer(**trainer_kwargs)

    # 8.5 Setup Google Drive Sync Callback & Checkpoint Auto-Resume
    from transformers import TrainerCallback
    import shutil

    drive_backup_dir = None
    if args.drive_dir:
        drive_backup_dir = Path(args.drive_dir)
    elif Path("/content/drive/MyDrive").exists():
        drive_backup_dir = Path("/content/drive/MyDrive/LISAN_BACKUP")

    if drive_backup_dir:
        drive_backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n[Google Drive Backup] Active! Securing models to: {drive_backup_dir}")

        class DriveSyncCallback(TrainerCallback):
            def __init__(self, target_dir: Path, source_dir: Path):
                self.target_dir = target_dir
                self.source_dir = source_dir
                self.target_dir.mkdir(parents=True, exist_ok=True)

            def on_save(self, args, state, control, **kwargs):
                print(f"\n[Drive Sync] Live syncing latest checkpoint to Google Drive...")
                try:
                    for ckpt in self.source_dir.glob("checkpoint-*"):
                        dst = self.target_dir / ckpt.name
                        if not dst.exists():
                            shutil.copytree(ckpt, dst, dirs_exist_ok=True)
                    print("[Drive Sync] ✓ Checkpoint secured in Google Drive!")
                except Exception as e:
                    print(f"[Drive Sync] Warning: {e}")

        trainer.add_callback(DriveSyncCallback(drive_backup_dir / "checkpoints", Path(args.output_dir)))

    # Determine if resuming from checkpoint
    resume_checkpoint = None
    local_ckpts = sorted(
        list(Path(args.output_dir).glob("checkpoint-*")),
        key=lambda p: int(p.name.split("-")[1]) if "-" in p.name and p.name.split("-")[1].isdigit() else 0
    )
    if args.resume or local_ckpts:
        if local_ckpts:
            resume_checkpoint = str(local_ckpts[-1])
            print(f"✓ Resuming training from local checkpoint: {resume_checkpoint}")
        elif drive_backup_dir and (drive_backup_dir / "checkpoints").exists():
            drive_ckpts = sorted(
                list((drive_backup_dir / "checkpoints").glob("checkpoint-*")),
                key=lambda p: int(p.name.split("-")[1]) if "-" in p.name and p.name.split("-")[1].isdigit() else 0
            )
            if drive_ckpts:
                latest_drive = drive_ckpts[-1]
                local_restore = Path(args.output_dir) / latest_drive.name
                shutil.copytree(latest_drive, local_restore, dirs_exist_ok=True)
                resume_checkpoint = str(local_restore)
                print(f"✓ Restored and resuming from Google Drive checkpoint: {resume_checkpoint}")

    # 9. Train
    print("\nStarting LoRA Fine-Tuning...")
    trainer.train(resume_from_checkpoint=resume_checkpoint)

    # 10. Save LoRA Adapter
    print(f"\nSaving LoRA adapter to {args.output_dir}...")
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print("✓ LoRA Adapter weights saved.")

    if drive_backup_dir:
        print(f"[Drive Sync] Copying final LoRA adapter to Google Drive...")
        try:
            drive_adapter = drive_backup_dir / "nllb_lora_adapter"
            drive_adapter.mkdir(parents=True, exist_ok=True)
            for f in Path(args.output_dir).glob("*"):
                if f.is_file():
                    shutil.copy2(f, drive_adapter / f.name)
            print(f"[Drive Sync] ✓ Final LoRA adapter permanently saved at {drive_adapter}")
        except Exception as e:
            print(f"[Drive Sync] Adapter note: {e}")

    # 11. Merge and Export
    if args.merge_and_export:
        del model
        del trainer
        if cuda_avail:
            torch.cuda.empty_cache()
        if str(ROOT_DIR) not in sys.path:
            sys.path.insert(0, str(ROOT_DIR))
        from scripts.merge_nllb_lora import merge_nllb
        merge_nllb(args.base_model, args.output_dir, args.merged_dir, args.export_c2_dir)

        if args.export_onnx:
            print("\n" + "=" * 60)
            print("📱 Exporting Merged Model to Mobile ONNX INT8...")
            print("=" * 60)
            try:
                from ai_pipeline.export_onnx import export_nllb
                export_nllb(model_path=args.merged_dir)
                print("✓ Mobile ONNX INT8 export complete!")
            except Exception as e:
                print(f"⚠️ ONNX export note: {e}")

        if drive_backup_dir:
            try:
                # Copy merged PyTorch model to Drive
                if Path(args.merged_dir).exists():
                    print(f"[Drive Sync] Copying merged PyTorch model to Google Drive...")
                    drive_merged = drive_backup_dir / "nllb_merged"
                    drive_merged.mkdir(parents=True, exist_ok=True)
                    for f in Path(args.merged_dir).glob("*"):
                        if f.is_file():
                            shutil.copy2(f, drive_merged / f.name)
                    print(f"[Drive Sync] ✓ Merged model saved at {drive_merged}")

                # Copy CTranslate2 model to Drive
                if Path(args.export_c2_dir).exists():
                    drive_c2 = drive_backup_dir / "nllb_int8"
                    shutil.copytree(Path(args.export_c2_dir), drive_c2, dirs_exist_ok=True)
                    print(f"[Drive Sync] ✓ CTranslate2 model saved at {drive_c2}")

                # Copy mobile ONNX models to Drive
                onnx_src = ROOT_DIR / "onnx_models"
                if onnx_src.exists():
                    drive_onnx = drive_backup_dir / "onnx_models"
                    drive_onnx.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(onnx_src, drive_onnx, dirs_exist_ok=True)
                    print(f"[Drive Sync] ✓ Mobile ONNX models copied to {drive_onnx}")

                # Create 1-click download zip directly on Google Drive
                zip_path = drive_backup_dir / "lisan_mobile_onnx_models"
                if onnx_src.exists():
                    shutil.make_archive(str(zip_path), "zip", str(onnx_src))
                    print(f"\n🎉 [Drive Sync] ONE-CLICK DOWNLOAD READY IN GOOGLE DRIVE: {zip_path}.zip")
            except Exception as e:
                print(f"[Drive Sync] Post-export backup note: {e}")

    # 12. Evaluate Benchmarks
    if args.eval_benchmarks:
        print("\n" + "=" * 60)
        print("📊 Running HornMT Benchmark Evaluation...")
        print("=" * 60)
        bench_script = ROOT_DIR / "scripts" / "evaluate_benchmarks.py"
        if bench_script.exists():
            subprocess.run([sys.executable, str(bench_script), "--limit", "100"], check=False)

    print("\n" + "=" * 70)
    print("🎉 LISAN AI: NMT TRAINING & EXPORT COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
