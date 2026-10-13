import sys
import os
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import copy
import time

def test_pruning():
    print("Loading base NLLB model...")
    model_name = "facebook/nllb-200-distilled-600M"
    tok = AutoTokenizer.from_pretrained(model_name)
    base_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    base_model.eval()

    test_sentences = [
        ("Where is the hospital?", "eng_Latn", "amh_Ethi"),
        ("I have severe abdominal pain.", "eng_Latn", "amh_Ethi"),
        ("Where is the nearest water?", "eng_Latn", "gaz_Latn"),
        ("ደህና ነዎት? ስምዎት ማን ነው?", "amh_Ethi", "eng_Latn"),
    ]

    print("\n--- BASELINE: Full 12 Encoder / 12 Decoder Layers ---")
    for text, src, tgt in test_sentences:
        tok.src_lang = src
        inputs = tok(text, return_tensors="pt")
        forced_bos = tok.convert_tokens_to_ids(tgt)
        t0 = time.time()
        with torch.no_grad():
            out = base_model.generate(**inputs, forced_bos_token_id=forced_bos, max_new_tokens=25)
        dt = time.time() - t0
        res = tok.batch_decode(out, skip_special_tokens=True)[0]
        print(f"[{src}->{tgt}] '{text}' -> '{res}' ({dt*1000:.1f}ms)")

    # Test layer pruning configurations
    # configs: (num_enc_layers, enc_indices, num_dec_layers, dec_indices)
    configs = [
        ("6 enc / 6 dec (every 2nd layer)", [0, 2, 4, 6, 8, 10], [0, 2, 4, 6, 8, 10]),
        ("4 enc / 4 dec (stride 3)", [0, 3, 6, 9], [0, 3, 6, 9]),
        ("3 enc / 3 dec (stride 4)", [0, 4, 8], [0, 4, 8]),
        ("4 enc / 2 dec", [0, 3, 6, 9], [0, 6]),
        ("first 3 enc / first 3 dec", [0, 1, 2], [0, 1, 2]),
    ]

    for name, enc_idx, dec_idx in configs:
        print(f"\n--- Testing Pruned Config: {name} ---")
        pruned_model = copy.deepcopy(base_model)
        pruned_model.model.encoder.layers = torch.nn.ModuleList([base_model.model.encoder.layers[i] for i in enc_idx])
        pruned_model.model.decoder.layers = torch.nn.ModuleList([base_model.model.decoder.layers[i] for i in dec_idx])
        pruned_model.config.encoder_layers = len(enc_idx)
        pruned_model.config.decoder_layers = len(dec_idx)
        for new_i, layer in enumerate(pruned_model.model.encoder.layers):
            if hasattr(layer.self_attn, 'layer_idx'):
                layer.self_attn.layer_idx = new_i
        for new_i, layer in enumerate(pruned_model.model.decoder.layers):
            if hasattr(layer.self_attn, 'layer_idx'):
                layer.self_attn.layer_idx = new_i
            if hasattr(layer.encoder_attn, 'layer_idx'):
                layer.encoder_attn.layer_idx = new_i

        for text, src, tgt in test_sentences:
            tok.src_lang = src
            inputs = tok(text, return_tensors="pt")
            forced_bos = tok.convert_tokens_to_ids(tgt)
            t0 = time.time()
            with torch.no_grad():
                out = pruned_model.generate(**inputs, forced_bos_token_id=forced_bos, max_new_tokens=25)
            dt = time.time() - t0
            res = tok.batch_decode(out, skip_special_tokens=True)[0]
            print(f"  [{src}->{tgt}] '{text}' -> '{res}' ({dt*1000:.1f}ms)")

if __name__ == "__main__":
    test_pruning()
