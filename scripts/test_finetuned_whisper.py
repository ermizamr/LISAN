import time
import torch
import soundfile as sf
from transformers import WhisperProcessor, WhisperForConditionalGeneration

def main():
    print("Loading finetuned whisper model...")
    processor = WhisperProcessor.from_pretrained("models_optimized/whisper_ethio_finetuned")
    model = WhisperForConditionalGeneration.from_pretrained("models_optimized/whisper_ethio_finetuned")
    model.eval()

    test_files = [
        ("test_speech.wav", "Amharic test"),
        ("test_oromo_tts.wav", "Oromo test"),
        ("ai_pipeline/test_audio/hello_en.wav", "English test"),
    ]

    for fpath, label in test_files:
        audio, sr = sf.read(fpath)
        inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
        t0 = time.time()
        with torch.no_grad():
            gen = model.generate(inputs.input_features)
        dur = time.time() - t0
        text = processor.batch_decode(gen, skip_special_tokens=True)[0]
        print(f"[{label}] Time: {dur:.2f}s | Decoded: '{text}'")

if __name__ == "__main__":
    main()
