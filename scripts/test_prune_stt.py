import time
import torch
import soundfile as sf
from transformers import AutoProcessor, Wav2Vec2BertForCTC

def test_prune():
    print("Loading processor & model...")
    processor = AutoProcessor.from_pretrained("onnx_models/ethio_stt")
    model = Wav2Vec2BertForCTC.from_pretrained("badrex/Ethio-ASR-multilingual-600M")
    model.eval()

    print(f"Original encoder layers: {len(model.wav2vec2_bert.encoder.layers)}")

    audio, sr = sf.read("test_speech.wav")
    inputs = processor(audio, sampling_rate=16000, return_tensors="pt")

    # 1. Full 24 layers
    with torch.no_grad():
        t0 = time.time()
        logits_full = model(**inputs).logits
        dur_full = time.time() - t0
        pred_full = logits_full.argmax(dim=-1)
        text_full = processor.batch_decode(pred_full)[0]
    print(f"[24 Layers] Time: {dur_full:.2f}s | Decoded: '{text_full}'")

    # 2. Prune to 12 layers
    model.wav2vec2_bert.encoder.layers = model.wav2vec2_bert.encoder.layers[:12]
    model.config.num_hidden_layers = 12
    with torch.no_grad():
        logits_12 = model(**inputs).logits
        pred_12 = logits_12.argmax(dim=-1)
        text_12 = processor.batch_decode(pred_12)[0]
    print(f"[12 Layers] Decoded: '{text_12}'")

    # 3. Prune to 6 layers
    model.wav2vec2_bert.encoder.layers = model.wav2vec2_bert.encoder.layers[:6]
    model.config.num_hidden_layers = 6
    with torch.no_grad():
        logits_6 = model(**inputs).logits
        pred_6 = logits_6.argmax(dim=-1)
        text_6 = processor.batch_decode(pred_6)[0]
    print(f"[6 Layers]  Decoded: '{text_6}'")

if __name__ == "__main__":
    test_prune()
