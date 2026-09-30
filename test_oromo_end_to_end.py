"""
Comprehensive verification test for Afaan Oromoo STT, Translation, and MMS-TTS.
Tests:
1. Dataset.ET Lexicon integration and Hudhaa normalization in SpeechRepair.
2. MMSTTSEngine synthesis to WAV bytes and file.
3. EthioMultilingualSTT dedicated Oromo beam search decoding.
4. FastAPI server /tts endpoints.
"""

import os
import sys
import io

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import soundfile as sf
from rich.console import Console

console = Console(highlight=False)

def test_speech_repair():
    console.print("\n[bold cyan]1. Testing SpeechRepair Qubee Normalization[/bold cyan]")
    from ai_pipeline.speech_repair import SpeechRepair
    repairer = SpeechRepair()

    # Test 1: Elongated disfluency collapse (preserving double vowels/consonants)
    raw = "baaaay’ee gaariii dha"
    repaired = repairer.repair(raw, "orm")
    console.print(f"  Raw:      '{raw}'")
    console.print(f"  Repaired: '{repaired}'")
    assert "baay'ee" in repaired, f"Expected baay'ee, got {repaired}"
    assert "gaarii" in repaired, f"Expected gaarii, got {repaired}"

    # Test 2: Hudhaa quote normalization
    raw_hudhaa = "har’a bal‘aa"
    repaired_hudhaa = repairer.repair(raw_hudhaa, "orm")
    console.print(f"  Raw:      '{raw_hudhaa}'")
    console.print(f"  Repaired: '{repaired_hudhaa}'")
    assert "har'a" in repaired_hudhaa
    assert "bal'aa" in repaired_hudhaa
    console.print("[bold green]✓ SpeechRepair Qubee tests passed![/bold green]")

def test_mms_tts():
    console.print("\n[bold cyan]2. Testing MMSTTSEngine Neural Synthesis[/bold cyan]")
    from ai_pipeline.pipeline import MMSTTSEngine
    tts = MMSTTSEngine()

    test_sentence = "Afaan Oromoo akka gaariitti dubbata."
    wav_bytes = tts.synthesize_to_bytes(test_sentence, lang="orm")
    console.print(f"  Generated Oromo audio: {len(wav_bytes):,} bytes")
    assert len(wav_bytes) > 20000, f"Expected >20k bytes for WAV, got {len(wav_bytes)}"

    # Check WAV headers
    data, sr = sf.read(io.BytesIO(wav_bytes))
    console.print(f"  Sample rate: {sr} Hz, Duration: {len(data)/sr:.2f}s")
    assert sr == 16000, f"Expected 16kHz, got {sr}"
    assert len(data) > 0

    # Save to scratch/test_oromo_pipeline.wav
    os.makedirs("scratch", exist_ok=True)
    out_path = "scratch/test_oromo_pipeline.wav"
    tts.synthesize_to_file(test_sentence, "orm", out_path)
    assert os.path.exists(out_path)
    console.print(f"[bold green]✓ MMSTTSEngine synthesis passed! Saved to {out_path}[/bold green]")
    return out_path

def test_stt_transcription(audio_path: str):
    console.print("\n[bold cyan]3. Testing EthioMultilingualSTT Dedicated Oromo Beam Decoder[/bold cyan]")
    from ai_pipeline.pipeline import EthioMultilingualSTT
    stt = EthioMultilingualSTT()
    stt.load()

    text = stt.transcribe(audio_path, language_code="om")
    console.print(f"  Transcribed: '{text}'")
    assert len(text.strip()) > 0, "Transcription should not be empty"
    console.print("[bold green]✓ EthioMultilingualSTT transcription passed![/bold green]")

def test_fastapi_tts():
    console.print("\n[bold cyan]4. Testing FastAPI Server /tts Endpoint[/bold cyan]")
    from fastapi.testclient import TestClient
    from server import app
    from ai_pipeline.pipeline import TranslatorPipeline

    if getattr(app.state, "pipeline", None) is None:
        pipeline = TranslatorPipeline()
        app.state.pipeline = pipeline

    with TestClient(app) as client:
        # Test GET /tts
        res_get = client.get("/tts", params={"text": "Nagaatti", "lang": "orm"})
        console.print(f"  GET /tts status: {res_get.status_code}, content-type: {res_get.headers.get('content-type')}")
        assert res_get.status_code == 200
        assert "audio/wav" in res_get.headers.get("content-type", "")
        assert len(res_get.content) > 10000

        # Test POST /tts
        res_post = client.post("/tts", json={"text": "Galatoomaa", "lang": "orm"})
        console.print(f"  POST /tts status: {res_post.status_code}, length: {len(res_post.content):,} bytes")
        assert res_post.status_code == 200
        assert len(res_post.content) > 10000

        console.print("[bold green]✓ FastAPI /tts endpoints passed![/bold green]")

if __name__ == "__main__":
    console.print("[bold magenta]==================================================[/bold magenta]")
    console.print("[bold magenta]  RUNNING COMPREHENSIVE AFAAN OROMOO VERIFICATION [/bold magenta]")
    console.print("[bold magenta]==================================================[/bold magenta]")
    test_speech_repair()
    audio_file = test_mms_tts()
    test_stt_transcription(audio_file)
    test_fastapi_tts()
    console.print("\n[bold green]==================================================[/bold green]")
    console.print("[bold green]  ALL AFAAN OROMOO PIPELINE TESTS PASSED 100%!    [/bold green]")
    console.print("[bold green]==================================================[/bold green]")
