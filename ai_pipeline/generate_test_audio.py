"""
Generate test WAV files at 16kHz using gTTS.
Converts MP3 bytes -> numpy PCM using the `miniaudio` library
which is pure Python and does NOT need FFmpeg.

Usage:
    python generate_test_audio.py
"""

import os
import io
import numpy as np
import soundfile as sf

TEST_PHRASES = [
    ("hello_en",    "Hello, my name is Ermi. I need help please.",  "en"),
    ("hospital_en", "Where is the nearest hospital?",               "en"),
    ("doctor_en",   "I need a doctor immediately.",                  "en"),
]

TARGET_SR = 16000  # Whisper expects 16kHz


def gtts_mp3_to_wav_array(text: str, lang: str):
    """
    Generate speech with gTTS (returns MP3 bytes),
    decode with miniaudio (pure Python, no FFmpeg),
    return numpy float32 array at TARGET_SR.
    """
    from gtts import gTTS
    import miniaudio

    # Generate MP3 in memory
    tts = gTTS(text=text, lang=lang, slow=False)
    mp3_buf = io.BytesIO()
    tts.write_to_fp(mp3_buf)
    mp3_buf.seek(0)
    mp3_bytes = mp3_buf.read()

    # Decode MP3 -> PCM with miniaudio (pure Python, no FFmpeg)
    decoded = miniaudio.decode(mp3_bytes, output_format=miniaudio.SampleFormat.FLOAT32)
    samples = np.frombuffer(decoded.samples, dtype=np.float32)

    # Mix to mono if stereo
    if decoded.nchannels > 1:
        samples = samples.reshape(-1, decoded.nchannels).mean(axis=1)

    # Resample to 16kHz if needed
    if decoded.sample_rate != TARGET_SR:
        import scipy.signal as sig
        num_out = int(len(samples) * TARGET_SR / decoded.sample_rate)
        samples = sig.resample(samples, num_out).astype(np.float32)

    return samples, TARGET_SR


def _write_silent_wav(output_path: str, duration: float = 3.0):
    """Write a silent 16kHz WAV as fallback."""
    samples = np.zeros(int(duration * TARGET_SR), dtype=np.float32)
    sf.write(output_path, samples, TARGET_SR)


def generate_test_wavs(output_dir="test_audio"):
    """Generate 16kHz WAV test files. Returns (output_dir, 'wav')."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"Generating {len(TEST_PHRASES)} test WAV files...")

    for name, text, lang in TEST_PHRASES:
        output_path = os.path.join(output_dir, f"{name}.wav")
        try:
            samples, sr = gtts_mp3_to_wav_array(text, lang)
            sf.write(output_path, samples, sr)
            print(f"  [OK]     {output_path}  ({text[:45]})")
        except Exception as e:
            print(f"  [SILENT] {output_path}  (fallback: {e})")
            _write_silent_wav(output_path)

    print(f"\nDone! Test WAVs in: ./{output_dir}/")
    return output_dir, "wav"


if __name__ == "__main__":
    generate_test_wavs()
