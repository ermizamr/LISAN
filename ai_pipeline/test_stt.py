"""
Day 2: Test Whisper STT
========================
Tests:
  1. Whisper model loads correctly
  2. Transcribes English audio accurately
  3. Measures transcription latency
  4. End-to-end: audio -> transcribe -> translate -> speak
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import time
import os
from pipeline import WhisperSTT, NLLB200Translator, SimpleTTS, LANGUAGES
from generate_test_audio import generate_test_wavs
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console(force_terminal=True, highlight=False)


def test_whisper_load():
    """Test 1: Whisper loads correctly."""
    console.print("\n[bold cyan]Test 1: Loading Whisper[/bold cyan]")
    stt = WhisperSTT(model_size="tiny")
    t = time.time()
    stt.load()
    load_time = time.time() - t
    console.print(f"[green]  Load time: {load_time:.2f}s[/green]")
    return stt


def test_whisper_transcription(stt):
    """Test 2: Transcribe generated test audio."""
    console.print("\n[bold cyan]Test 2: Transcription Accuracy[/bold cyan]")

    audio_dir, fmt = generate_test_wavs()

    test_cases = [
        ("hello_en",    "Hello, my name is Ermi. I need help please.", "en"),
        ("hospital_en", "Where is the nearest hospital?",               "en"),
        ("doctor_en",   "I need a doctor immediately.",                  "en"),
    ]

    table = Table(title="Whisper Transcription Results", show_lines=True)
    table.add_column("Expected", style="cyan", max_width=35)
    table.add_column("Transcribed", style="green", max_width=35)
    table.add_column("Time", style="yellow")

    results = []
    for name, expected, lang in test_cases:
        audio_path = os.path.join(audio_dir, f"{name}.{fmt}")
        if not os.path.exists(audio_path):
            console.print(f"[red]  Missing: {audio_path}[/red]")
            continue

        t = time.time()
        transcribed = stt.transcribe(audio_path, lang)
        elapsed = time.time() - t

        table.add_row(expected[:35], transcribed[:35] if transcribed else "[silent/empty]", f"{elapsed:.2f}s")
        results.append({
            "expected": expected,
            "transcribed": transcribed,
            "latency": elapsed
        })

    console.print(table)
    return results, audio_dir, fmt


def test_end_to_end(stt, translator, tts, audio_file, src_lang, tgt_lang):
    """Test 3: Full pipeline - audio -> STT -> translate -> speak."""
    console.print(f"\n[bold cyan]Test 3: End-to-End Pipeline[/bold cyan]")
    console.print(f"  Audio: {audio_file}")
    console.print(f"  Direction: {src_lang} -> {tgt_lang}\n")

    src = LANGUAGES[src_lang]
    tgt = LANGUAGES[tgt_lang]

    # STT
    t0 = time.time()
    whisper_lang = src["whisper_code"] or "en"
    text = stt.transcribe(audio_file, whisper_lang)
    stt_time = time.time() - t0
    console.print(f"  [cyan]STT ({stt_time:.2f}s):[/cyan] '{text}'")

    if not text.strip():
        console.print("  [yellow]Empty transcription (silent audio). Skipping translation.[/yellow]")
        console.print("  [dim]Tip: Record a real voice sample for accurate STT testing.[/dim]")
        return {"stt_latency": stt_time, "total_latency": stt_time, "source_text": "", "translated_text": ""}

    # Translation
    t1 = time.time()
    translated = translator.translate(text, src["nllb_code"], tgt["nllb_code"])
    trans_time = time.time() - t1
    console.print(f"  [cyan]Translation ({trans_time:.2f}s):[/cyan] '{translated}'")

    # TTS - speak only (no save, avoids Windows hang)
    t2 = time.time()
    tts.speak(translated)
    tts_time = time.time() - t2
    console.print(f"  [cyan]TTS ({tts_time:.2f}s):[/cyan] Spoken aloud")

    total = time.time() - t0
    console.print(f"\n  [bold green]Total latency: {total:.2f}s[/bold green]")

    return {
        "stt_latency": stt_time,
        "translation_latency": trans_time,
        "tts_latency": tts_time,
        "total_latency": total,
        "source_text": text,
        "translated_text": translated,
    }


def run_all_tests():
    console.print(Panel(
        "Day 2: Whisper STT Tests\n"
        "Testing speech recognition pipeline",
        expand=False
    ))

    # Load all models
    console.print("\n[bold]Loading models...[/bold]")
    stt = test_whisper_load()

    translator = NLLB200Translator()
    translator.load()

    tts = SimpleTTS()
    tts.load()

    # Transcription test
    results, audio_dir, fmt = test_whisper_transcription(stt)

    # End-to-end test: English audio -> Amharic speech
    audio_file = os.path.join(audio_dir, f"hospital_en.{fmt}")
    if os.path.exists(audio_file):
        e2e = test_end_to_end(stt, translator, tts, audio_file, "eng", "amh")

        if e2e.get("total_latency"):
            console.print(Panel(
                f"Latency Benchmark\n"
                f"  STT (Whisper tiny):  {e2e.get('stt_latency', 0):.2f}s\n"
                f"  Translation (NLLB):  {e2e.get('translation_latency', 0):.2f}s\n"
                f"  TTS (pyttsx3):       {e2e.get('tts_latency', 0):.2f}s\n"
                f"  Total end-to-end:    {e2e['total_latency']:.2f}s",
                title="Performance",
                expand=False
            ))

    console.print("\n[bold green]Day 2 complete![/bold green]")
    console.print("[dim]Next: Wire microphone for live voice translation[/dim]")


if __name__ == "__main__":
    run_all_tests()
