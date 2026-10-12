import os
from pathlib import Path

hub = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub"
p_tir = sorted((hub / "models--facebook--mms-tts-tir" / "snapshots").iterdir())[-1]

from transformers import AutoTokenizer, VitsModel
import torch

print(f"Loading from: {p_tir}")
tok = AutoTokenizer.from_pretrained(str(p_tir), local_files_only=True)
mod = VitsModel.from_pretrained(str(p_tir), local_files_only=True)
mod.eval()

print("Model and Tokenizer loaded!")
print("Vocab:", tok.get_vocab())

# Test text
text = "selam"
inputs = tok(text, return_tensors="pt")
print("Inputs for 'selam':", inputs)
with torch.no_grad():
    out = mod(**inputs).waveform
print("Output waveform shape:", out.shape)
