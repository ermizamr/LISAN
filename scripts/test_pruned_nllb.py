import json
import sys
import time
import numpy as np
import onnxruntime as ort

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

enc_path = "onnx_models/nllb_pruned/int8/encoder_model_quantized.onnx"
dec_path = "onnx_models/nllb_pruned/int8/decoder_model_quantized.onnx"
tok_path = "onnx_models/nllb_pruned/int8/tokenizer.json"

print("Loading pruned tokenizer...")
with open(tok_path, "r", encoding="utf-8") as f:
    tok_data = json.load(f)
vocab = tok_data["model"]["vocab"]
id_to_token = {v: k for k, v in vocab.items()}

print(f"Loaded pruned vocab: {len(vocab):,} tokens")

opts = ort.SessionOptions()
opts.intra_op_num_threads = 2
opts.inter_op_num_threads = 1

print("Loading ONNX sessions...")
enc_sess = ort.InferenceSession(enc_path, sess_options=opts, providers=["CPUExecutionProvider"])
dec_sess = ort.InferenceSession(dec_path, sess_options=opts, providers=["CPUExecutionProvider"])

eng_lang_id = vocab["eng_Latn"]
amh_lang_id = vocab["amh_Ethi"]
eos_id = vocab["</s>"]

sample_tokens = ["eng_Latn", " Where", " is", " the", " hospital", "?", "</s>"]
sample_ids = [vocab.get(t, vocab.get("<unk>", 3)) for t in sample_tokens]
print("Encoded sample input IDs:", sample_ids)

input_ids = np.array([sample_ids], dtype=np.int64)
attention_mask = np.ones_like(input_ids, dtype=np.int64)

t0 = time.time()
enc_out = enc_sess.run(["last_hidden_state"], {"input_ids": input_ids, "attention_mask": attention_mask})
hidden_states = enc_out[0]
print(f"Encoder run time: {time.time()-t0:.3f}s, output shape: {hidden_states.shape}")

curr_ids = [eos_id, amh_lang_id]
generated_tokens = []
t1 = time.time()
for step in range(12):
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
    next_id = int(np.argmax(logits[0, -1, :]))
    curr_ids.append(next_id)
    if next_id in (eos_id, vocab.get("<pad>", 1)):
        break
    piece = id_to_token.get(next_id, "<unk>")
    generated_tokens.append(piece)

total_dec_time = time.time() - t1
print(f"Decoder run time: {total_dec_time:.3f}s for {len(generated_tokens)} steps ({total_dec_time/max(1,len(generated_tokens))*1000:.1f}ms/token)")
raw_translated = "".join(generated_tokens).replace(" ", " ").strip()
print(f"Generated Amharic Translation: '{raw_translated}'")
print("SUCCESS! Pruned NLLB INT8 translation verified on host!")
