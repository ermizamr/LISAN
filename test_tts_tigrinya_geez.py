import os
from pathlib import Path

hub = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub"
p_tir = sorted((hub / "models--facebook--mms-tts-tir" / "snapshots").iterdir())[-1]

from transformers import AutoTokenizer, VitsModel
import torch

tok = AutoTokenizer.from_pretrained(str(p_tir), local_files_only=True)
mod = VitsModel.from_pretrained(str(p_tir), local_files_only=True)
mod.eval()

tir_text = "ሰላም! እዚ ጥንታዊ ናይ ሓወልቲ ግራናይት ኣዝዩ ዘደንቕ እዩ። ዕድሚኡ ክንደይ ዓመት እዩ?"
inputs = tok(tir_text, return_tensors="pt")
print("Tigrinya Ge'ez inputs:", inputs)
with torch.no_grad():
    out = mod(**inputs).waveform
print("Output shape:", out.shape)
