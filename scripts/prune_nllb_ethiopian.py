"""
Prune and Quantize NLLB-200 for Ethiopian Languages (Amharic, Oromo, Tigrinya, Somali, English)
=============================================================================================
Prunes the 256,206 NLLB vocabulary down to ~15,000-25,000 tokens covering:
1. Special tokens: <s> (0), <pad> (1), </s> (2), <unk> (3)
2. Target language tokens: amh_Ethi, gaz_Latn, tir_Ethi, som_Latn, eng_Latn
3. All 3,652 Ethiopic script tokens (complete Ge'ez fidel coverage)
4. All single ASCII, Latin, digits, and punctuation characters (zero unk fallback)
5. All domain tokens from validation, training datasets, and medical glossaries

Then performs surgical initializer slicing on ONNX encoder & decoder,
quantizes to INT8, enforces ONNX IR version 9, and outputs compact models.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


import numpy as np
import onnx
from onnx import numpy_helper
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType
from transformers import AutoTokenizer

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_NLLB_DIR = ROOT_DIR / "onnx_models" / "nllb"
OUT_PRUNED_DIR = ROOT_DIR / "onnx_models" / "nllb_pruned"
OUT_INT8_DIR = OUT_PRUNED_DIR / "int8"

TARGET_LANGS = {
    "amh_Ethi",  # Amharic
    "gaz_Latn",  # Afaan Oromoo
    "tir_Ethi",  # Tigrinya
    "som_Latn",  # Somali
    "eng_Latn",  # English
}


def build_pruned_vocab(tok: AutoTokenizer) -> tuple[list[int], dict[int, int]]:
    print("Building pruned vocabulary for Ethiopian languages...")
    vocab = tok.get_vocab()
    needed_ids = set()

    # 1. Base special tokens (IDs 0, 1, 2, 3 must remain at positions 0, 1, 2, 3)
    for tid in [0, 1, 2, 3]:
        needed_ids.add(tid)

    # 2. Target language tokens
    for lang in TARGET_LANGS:
        if lang in vocab:
            needed_ids.add(vocab[lang])
        if f"__{lang}__" in vocab:
            needed_ids.add(vocab[f"__{lang}__"])
    print(f"  • Included {len(TARGET_LANGS)} target language tokens")


    # 3. All Ethiopic tokens
    ethiopic_count = 0
    for t, tid in vocab.items():
        if any(0x1200 <= ord(c) <= 0x139F or 0x2D80 <= ord(c) <= 0x2DDF or 0xAB00 <= ord(c) <= 0xAB2F for c in t):
            needed_ids.add(tid)
            ethiopic_count += 1
    print(f"  • Included {ethiopic_count} Ethiopic script tokens")

    # 4. All single ASCII, Latin characters, numbers, and basic punctuation
    for t, tid in vocab.items():
        clean = t.replace(" ", "")
        if len(clean) == 1 and (ord(clean) < 256):
            needed_ids.add(tid)

    # 5. Tokens from validation dataset
    val_path = ROOT_DIR / "data" / "training_data" / "val.jsonl"
    if val_path.exists():
        pair_count = 0
        with open(val_path, "r", encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                for text in [row.get("source", ""), row.get("target", "")]:
                    if text:
                        needed_ids.update(tok.encode(text, add_special_tokens=False))
                pair_count += 1
        print(f"  • Ingested {pair_count} sentence pairs from val.jsonl")

    # 6. Tokens from training dataset (first 25,000 sentences)
    train_path = ROOT_DIR / "data" / "training_data" / "train.jsonl"
    if train_path.exists():
        pair_count = 0
        with open(train_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 25000:
                    break
                row = json.loads(line)
                for text in [row.get("source", ""), row.get("target", "")]:
                    if text:
                        needed_ids.update(tok.encode(text, add_special_tokens=False))
                pair_count += 1
        print(f"  • Ingested {pair_count} sentence pairs from train.jsonl")

    # 7. Tokens from offline translation memory
    tm_path = ROOT_DIR / "ethiopian_translator" / "lib" / "offline_translation_memory.dart"
    if tm_path.exists():
        with open(tm_path, "r", encoding="utf-8") as f:
            content = f.read()
        strings = re.findall(r"'([^'\\\\]*(?:\\\\.[^'\\\\]*)*)'", content)
        for s in strings:
            if len(s) > 1 and not s.startswith("package:") and not s.startswith("assets/"):
                needed_ids.update(tok.encode(s, add_special_tokens=False))
        print("  • Ingested medical glossaries from offline_translation_memory.dart")

    sorted_needed = sorted(list(needed_ids))
    # Double check that indices 0, 1, 2, 3 are mapped 1-to-1
    assert sorted_needed[0] == 0 and sorted_needed[1] == 1 and sorted_needed[2] == 2 and sorted_needed[3] == 3, (
        f"Special tokens order mismatch: {sorted_needed[:4]}"
    )

    old_to_new = {old: new for new, old in enumerate(sorted_needed)}
    print(f"✓ Pruned vocab size: {len(sorted_needed):,} tokens (down from {len(vocab):,}, {(1 - len(sorted_needed)/len(vocab))*100:.1f}% reduction)")
    return sorted_needed, old_to_new


def prune_tokenizer_json(
    tok: AutoTokenizer,
    kept_ids: list[int],
    old_to_new: dict[int, int],
    out_file: Path,
):
    print("Pruning tokenizer.json...")
    tok_json_path = SRC_NLLB_DIR / "tokenizer.json"
    with open(tok_json_path, "r", encoding="utf-8") as f:
        tok_data = json.load(f)

    inv_vocab = {v: k for k, v in tok.get_vocab().items()}
    new_vocab = {}
    for new_id, old_id in enumerate(kept_ids):
        token_str = inv_vocab[old_id]
        new_vocab[token_str] = new_id

    tok_data["model"]["vocab"] = new_vocab

    # Prune merges
    old_merges = tok_data["model"].get("merges", [])
    new_merges = []
    for m in old_merges:
        if isinstance(m, list):
            part1, part2 = m[0], m[1]
        elif isinstance(m, str):
            parts = m.split(" ")
            if len(parts) >= 2:
                part1, part2 = parts[0], parts[1]
            else:
                continue
        else:
            continue
        
        merged_piece = part1 + part2
        # Keep merge if both parts exist or merged piece exists in new_vocab
        if (part1 in new_vocab and part2 in new_vocab) or (merged_piece in new_vocab):
            new_merges.append(m)

    tok_data["model"]["merges"] = new_merges
    print(f"  • Pruned merges: {len(new_merges):,} (down from {len(old_merges):,})")

    # Update added_tokens
    if "added_tokens" in tok_data:
        new_added = []
        for at in tok_data["added_tokens"]:
            content = at.get("content", "")
            if content in new_vocab:
                at_copy = dict(at)
                at_copy["id"] = new_vocab[content]
                new_added.append(at_copy)
        tok_data["added_tokens"] = new_added

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(tok_data, f, ensure_ascii=False)

    mb = out_file.stat().st_size / 1e6
    print(f"✓ Saved pruned tokenizer.json ({mb:.2f} MB) -> {out_file}")


def prune_encoder(kept_ids: list[int], out_file: Path):
    print("Pruning encoder ONNX model...")
    t0 = time.time()
    enc_path = SRC_NLLB_DIR / "encoder_model.onnx"
    model = onnx.load(str(enc_path), load_external_data=True)

    # Find embed_tokens.weight
    embed_init = None
    for init in model.graph.initializer:
        if init.name == "embed_tokens.weight":
            embed_init = init
            break

    if embed_init is None:
        raise ValueError("Could not find embed_tokens.weight in encoder_model.onnx")

    w = numpy_helper.to_array(embed_init)
    print(f"  • Original encoder embed shape: {w.shape}")
    w_pruned = w[kept_ids, :]
    print(f"  • Pruned encoder embed shape: {w_pruned.shape}")

    new_init = numpy_helper.from_array(w_pruned, name="embed_tokens.weight")
    model.graph.initializer.remove(embed_init)
    model.graph.initializer.append(new_init)

    # Force IR version 9 for Flutter onnxruntime compatibility
    model.ir_version = 9

    out_file.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(out_file))
    print(f"✓ Pruned encoder saved in {time.time()-t0:.1f}s ({out_file.stat().st_size / 1e6:.1f} MB) -> {out_file}")


def prune_decoder(kept_ids: list[int], out_file: Path):
    print("Pruning decoder ONNX model...")
    t0 = time.time()
    dec_path = SRC_NLLB_DIR / "decoder_model.onnx"
    model = onnx.load(str(dec_path), load_external_data=True)

    # 1. model.shared.weight
    shared_init = None
    for init in model.graph.initializer:
        if init.name == "model.shared.weight":
            shared_init = init
            break

    if shared_init is None:
        raise ValueError("Could not find model.shared.weight in decoder_model.onnx")

    w_shared = numpy_helper.to_array(shared_init)
    print(f"  • Original decoder shared embed shape: {w_shared.shape}")
    w_shared_pruned = w_shared[kept_ids, :]
    print(f"  • Pruned decoder shared embed shape: {w_shared_pruned.shape}")

    new_shared_init = numpy_helper.from_array(w_shared_pruned, name="model.shared.weight")
    model.graph.initializer.remove(shared_init)
    model.graph.initializer.append(new_shared_init)

    # 2. lm_head weight (onnx::MatMul_3416)
    lm_head_init = None
    for init in model.graph.initializer:
        if init.name == "onnx::MatMul_3416":
            lm_head_init = init
            break

    if lm_head_init is None:
        raise ValueError("Could not find onnx::MatMul_3416 in decoder_model.onnx")

    w_lm = numpy_helper.to_array(lm_head_init)
    print(f"  • Original decoder lm_head shape: {w_lm.shape}")
    w_lm_pruned = w_lm[:, kept_ids]
    print(f"  • Pruned decoder lm_head shape: {w_lm_pruned.shape}")

    new_lm_init = numpy_helper.from_array(w_lm_pruned, name="onnx::MatMul_3416")
    model.graph.initializer.remove(lm_head_init)
    model.graph.initializer.append(new_lm_init)

    # 3. Update logits output shape
    for out in model.graph.output:
        if out.name == "logits":
            out.type.tensor_type.shape.dim[2].dim_value = len(kept_ids)
            print(f"  • Updated logits output dim[2] -> {len(kept_ids)}")

    # Force IR version 9 for Flutter onnxruntime compatibility
    model.ir_version = 9

    out_file.parent.mkdir(parents=True, exist_ok=True)
    # Save model. If > 2GB (unlikely once pruned), save with external data
    if w_shared_pruned.nbytes + w_lm_pruned.nbytes > 1.8e9:
        onnx.save(model, str(out_file), save_as_external_data=True, all_tensors_to_one_file=True, location=f"{out_file.name}_data")
    else:
        onnx.save(model, str(out_file))

    print(f"✓ Pruned decoder saved in {time.time()-t0:.1f}s ({out_file.stat().st_size / 1e6:.1f} MB) -> {out_file}")


def quantize_pruned_models():
    print("\nQuantizing pruned ONNX models to INT8...")
    OUT_INT8_DIR.mkdir(parents=True, exist_ok=True)

    import onnxruntime.quantization.quant_utils as quant_utils
    import onnxruntime.quantization
    quant_mod = sys.modules["onnxruntime.quantization.quantize"]

    orig_load = quant_utils.load_model_with_shape_infer
    def patched_load(path):
        p = Path(path)
        m = orig_load(p)
        if not m.opset_import:
            orig_m = onnx.load(str(p), load_external_data=False)
            m.opset_import.extend(orig_m.opset_import)
        return m

    quant_utils.load_model_with_shape_infer = patched_load
    quant_mod.load_model_with_shape_infer = patched_load

    enc_src = OUT_PRUNED_DIR / "encoder_model.onnx"
    enc_dst = OUT_INT8_DIR / "encoder_model_quantized.onnx"
    print(f"Quantizing encoder: {enc_src.name} -> {enc_dst.name}...")
    t0 = time.time()
    quant_mod.quantize_dynamic(
        model_input=str(enc_src),
        model_output=str(enc_dst),
        weight_type=QuantType.QInt8,
    )
    # Force IR version 9 on quantized model
    enc_m = onnx.load(str(enc_dst))
    enc_m.ir_version = 9
    onnx.save(enc_m, str(enc_dst))
    print(f"✓ Encoder INT8 created in {time.time()-t0:.1f}s ({enc_dst.stat().st_size / 1e6:.1f} MB)")

    dec_src = OUT_PRUNED_DIR / "decoder_model.onnx"
    dec_dst = OUT_INT8_DIR / "decoder_model_quantized.onnx"
    print(f"Quantizing decoder: {dec_src.name} -> {dec_dst.name}...")
    t0 = time.time()
    quant_mod.quantize_dynamic(
        model_input=str(dec_src),
        model_output=str(dec_dst),
        weight_type=QuantType.QInt8,
    )
    # Force IR version 9 on quantized model
    dec_m = onnx.load(str(dec_dst))
    dec_m.ir_version = 9
    onnx.save(dec_m, str(dec_dst))
    print(f"✓ Decoder INT8 created in {time.time()-t0:.1f}s ({dec_dst.stat().st_size / 1e6:.1f} MB)")

    # Copy tokenizer.json to int8 dir
    shutil.copy2(OUT_PRUNED_DIR / "tokenizer.json", OUT_INT8_DIR / "tokenizer.json")
    print("✓ Copied pruned tokenizer.json to int8 directory")


def verify_pruned_translation():
    print("\nVerifying pruned INT8 NMT on host CPU...")
    enc_path = OUT_INT8_DIR / "encoder_model_quantized.onnx"
    dec_path = OUT_INT8_DIR / "decoder_model_quantized.onnx"
    tok_path = OUT_INT8_DIR / "tokenizer.json"

    with open(tok_path, "r", encoding="utf-8") as f:
        tok_data = json.load(f)
    vocab = tok_data["model"]["vocab"]
    id_to_token = {v: k for k, v in vocab.items()}

    print(f"  • Loaded vocab size: {len(vocab):,}")

    # Check key tokens
    for t in ["amh_Ethi", "eng_Latn", "<s>", "</s>", "<pad>", "<unk>", " የት", " ውሃ", " water"]:
        print(f"  • Token '{t}' id: {vocab.get(t)}")

    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 2
    opts.inter_op_num_threads = 1
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

    print("Loading ONNX sessions...")
    enc_sess = ort.InferenceSession(str(enc_path), sess_options=opts, providers=["CPUExecutionProvider"])
    dec_sess = ort.InferenceSession(str(dec_path), sess_options=opts, providers=["CPUExecutionProvider"])

    # Test dummy translation: "Where is the clinic?"
    # English prompt: [eng_Latn, token1, token2, ..., </s>]
    eng_lang_id = vocab["eng_Latn"]
    amh_lang_id = vocab["amh_Ethi"]
    eos_id = vocab["</s>"]

    # Simple sample token ids
    sample_ids = [eng_lang_id, vocab.get(" Where", 3), vocab.get(" is", 3), vocab.get(" the", 3), eos_id]
    input_ids = np.array([sample_ids], dtype=np.int64)
    attention_mask = np.ones_like(input_ids, dtype=np.int64)

    t0 = time.time()
    enc_out = enc_sess.run(["last_hidden_state"], {"input_ids": input_ids, "attention_mask": attention_mask})
    hidden_states = enc_out[0]
    enc_time = time.time() - t0
    print(f"✓ Encoder forward pass successful in {enc_time:.3f}s, shape: {hidden_states.shape}")

    # Decoder generation
    curr_ids = [eos_id, amh_lang_id]
    generated_tokens = []
    t_dec_start = time.time()

    for step in range(8):
        dec_input_ids = np.array([curr_ids], dtype=np.int64)
        dec_out = dec_sess.run(
            ["logits"],
            {
                "input_ids": dec_input_ids,
                "encoder_attention_mask": attention_mask,
                "encoder_hidden_states": hidden_states,
            },
        )
        logits = dec_out[0]
        next_token_id = int(np.argmax(logits[0, -1, :]))
        curr_ids.append(next_token_id)
        if next_token_id == eos_id:
            break
        piece = id_to_token.get(next_token_id, "<unk>")
        generated_tokens.append(piece)

    dec_time = time.time() - t_dec_start
    print(f"✓ Decoder generation pass successful in {dec_time:.3f}s ({len(generated_tokens)} tokens)")
    translated_text = "".join(generated_tokens).replace(" ", " ").strip()
    print(f"✓ Output: '{translated_text}' (Token IDs: {curr_ids})")
    print("✓ Pruned NLLB Engine hardware verification ready!")


def main():
    print("=" * 70)
    print("  LISAN: NLLB-200 Pruning & INT8 Quantization Workflow")
    print("=" * 70)

    tok = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
    kept_ids, old_to_new = build_pruned_vocab(tok)

    prune_tokenizer_json(tok, kept_ids, old_to_new, OUT_PRUNED_DIR / "tokenizer.json")
    prune_encoder(kept_ids, OUT_PRUNED_DIR / "encoder_model.onnx")
    prune_decoder(kept_ids, OUT_PRUNED_DIR / "decoder_model.onnx")
    quantize_pruned_models()
    verify_pruned_translation()

    print("\n" + "=" * 70)
    print(f"✓ Pruned & Quantized NLLB Engine ready at: {OUT_INT8_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
