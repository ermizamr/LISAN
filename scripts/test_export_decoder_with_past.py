import sys
import os
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import torch
from transformers import AutoModelForSeq2SeqLM

def test_export():
    print("Loading NLLB model...")
    model_name = "facebook/nllb-200-distilled-600M"
    m = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    m.eval()

    class DecoderWithPastWrapper(torch.nn.Module):
        def __init__(self, decoder, lm_head):
            super().__init__()
            self.decoder = decoder
            self.lm_head = lm_head

        def forward(self, input_ids, encoder_attention_mask, past_key_values):
            # unpack past_key_values tuple
            outputs = self.decoder(
                input_ids=input_ids,
                encoder_attention_mask=encoder_attention_mask,
                past_key_values=past_key_values,
                use_cache=True,
            )
            logits = self.lm_head(outputs.last_hidden_state)
            return logits, outputs.past_key_values

    wrapper = DecoderWithPastWrapper(m.model.decoder, m.lm_head)
    
    # Test step 0
    inp0 = torch.tensor([[2, 256047]])
    enc_mask = torch.tensor([[1, 1, 1, 1, 1]])
    enc_hidden = torch.randn(1, 5, 1024)
    
    # Run step 0 to get initial past_key_values
    out0 = m.model.decoder(input_ids=inp0, encoder_hidden_states=enc_hidden, encoder_attention_mask=enc_mask, use_cache=True)
    pkv = out0.past_key_values
    
    # Test step 1
    inp1 = torch.tensor([[100]])
    with torch.no_grad():
        logits1, pkv1 = wrapper(inp1, enc_mask, pkv)
    print("✓ Wrapper forward pass successful!")
    print("  logits shape:", logits1.shape)
    print("  pkv1 len:", len(pkv1))
    print("  pkv1[0] shapes:", [x.shape for x in pkv1[0]])

if __name__ == "__main__":
    test_export()
