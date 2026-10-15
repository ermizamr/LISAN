import os
from pathlib import Path

hub = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub"
p_amh = sorted((hub / "models--facebook--mms-tts-amh" / "snapshots").iterdir())[-1]

from transformers import AutoTokenizer, VitsModel
import torch

tok = AutoTokenizer.from_pretrained(str(p_amh), local_files_only=True)
mod = VitsModel.from_pretrained(str(p_amh), local_files_only=True)
mod.eval()

text = "እንደምን ዋልክ"
inputs = tok(text, return_tensors="pt")
print("Amharic text inputs:", inputs)
with torch.no_grad():
    out = mod(**inputs).waveform
print("Output shape:", out.shape)
