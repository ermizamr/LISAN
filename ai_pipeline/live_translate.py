"""
Day 3: Live Microphone Conversation Mode
=========================================
Two people holding one phone, speaking different languages.
Press ENTER to start recording, release to translate.

Usage:
    python live_translate.py
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import time
import tempfile
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
from pipeline import TranslatorPipeline, LANGUAGES
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(force_terminal=True, highlight=False)

SAMPLE_RATE = 16000


def record_until_enter(sample_rate: int = SAMPLE_RATE, max_seconds: int = 10) -> str:
    """
    Record audio from mic until user presses ENTER (or max_seconds).
    Returns path to WAV file.
    """
    console.print("[yellow]  Recording... press ENTER to stop[/yellow]")

    frames = []
    stop_flag = [False]

    def callback(indata, frame_count, time_info, status):
        if not stop_flag[0]:
            frames.append(indata.copy())

    import threading
    def wait_for_enter():
        input()
        stop_flag[0] = True

    t = threading.Thread(target=wait_for_enter, daemon=True)
    t.start()

    with sd.InputStream(samplerate=sample_rate, channels=1,
                        dtype='float32', callback=callback):
        # Wait until ENTER pressed or max time reached
        start = time.time()
        while not stop_flag[0] and (time.time() - start) < max_seconds:
            time.sleep(0.05)

    if not frames:
        return None

    audio = np.concatenate(frames, axis=0).flatten()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sample_rate)
    return tmp.name


def conversation_loop(pipeline: TranslatorPipeline):
    """
    Interactive walkie-talkie conversation between two language speakers.
    """
    console.print(Panel(
        "CONVERSATION MODE\n"
        "Two people, one phone, real-time translation\n"
        "Press ENTER after each person speaks",
        expand=False
    ))

    # Language setup
    console.print("\n[bold]Available languages:[/bold]")
    for key, lang in LANGUAGES.items():
        console.print(f"  [cyan]{key}[/cyan]  {lang['name']} ({lang['native']})")

    console.print()
    person_a_lang = input("Person A language (e.g. eng): ").strip()
    person_b_lang = input("Person B language (e.g. amh): ").strip()

    if person_a_lang not in LANGUAGES or person_b_lang not in LANGUAGES:
        console.print("[red]Invalid language codes. Exiting.[/red]")
        return

    lang_a = LANGUAGES[person_a_lang]
    lang_b = LANGUAGES[person_b_lang]

    history = []
    turn = "A"

    console.print(Panel(
        f"Starting conversation:\n"
        f"  Person A: {lang_a['name']}\n"
        f"  Person B: {lang_b['name']}\n\n"
        f"Type 'q' + ENTER to quit",
        expand=False
    ))

    while True:
        if turn == "A":
            speaker_lang = person_a_lang
            target_lang = person_b_lang
            speaker_name = f"Person A ({lang_a['name']})"
            target_name = f"Person B ({lang_b['name']})"
        else:
            speaker_lang = person_b_lang
            target_lang = person_a_lang
            speaker_name = f"Person B ({lang_b['name']})"
            target_name = f"Person A ({lang_a['name']})"

        console.print(f"\n[bold cyan]{speaker_name}'s turn[/bold cyan]")
        console.print(f"  Press ENTER to start, then ENTER again to stop recording")
        console.print(f"  (or type 'q' and ENTER to quit)")

        cmd = input().strip().lower()
        if cmd == 'q':
            break

        # Record
        audio_path = record_until_enter()
        if not audio_path:
            console.print("[red]  No audio recorded.[/red]")
            continue

        # Transcribe
        t0 = time.time()
        src_lang = LANGUAGES[speaker_lang]
        whisper_lang = src_lang["whisper_code"] or "en"
        console.print(f"[cyan]  Transcribing...[/cyan]")
        text = pipeline.stt.transcribe(audio_path, whisper_lang)
        os.unlink(audio_path)

        if not text.strip():
            console.print("[yellow]  Could not understand audio. Try again.[/yellow]")
            continue

        console.print(f"  Heard: [italic]{text}[/italic]")

        # Translate
        console.print(f"[cyan]  Translating to {LANGUAGES[target_lang]['name']}...[/cyan]")
        translated = pipeline.translate_text(text, speaker_lang, target_lang)
        total_time = time.time() - t0
        console.print(f"  Translation: [bold green]{translated}[/bold green]")
        console.print(f"  [dim]({total_time:.1f}s)[/dim]")

        # Speak translation for the other person to hear
        console.print(f"[cyan]  Speaking for {target_name}...[/cyan]")
        pipeline.tts.speak(translated)

        # Store history
        history.append({
            "speaker": speaker_name,
            "original": text,
            "translated": translated,
            "target": target_name,
        })

        # Switch turns
        turn = "B" if turn == "A" else "A"

    # Print conversation history
    if history:
        console.print("\n[bold]Conversation Summary:[/bold]")
        table = Table(show_lines=True)
        table.add_column("Speaker", style="cyan")
        table.add_column("Said", style="white")
        table.add_column("Heard by", style="yellow")
        table.add_column("Translation", style="green")

        for h in history:
            table.add_row(h["speaker"], h["original"][:40],
                          h["target"], h["translated"][:40])
        console.print(table)


def main():
    console.print(Panel(
        "Ethiopian Language Translator\n"
        "Offline | Real-time | Multi-language",
        expand=False
    ))

    console.print("\n[bold]Loading AI models (this takes ~15s on first run)...[/bold]")
    pipeline = TranslatorPipeline(whisper_size="tiny")
    pipeline.load_all()

    while True:
        console.print("\n[bold]Choose mode:[/bold]")
        console.print("  [cyan]1[/cyan]  Quick text translation")
        console.print("  [cyan]2[/cyan]  Live microphone (single phrase)")
        console.print("  [cyan]3[/cyan]  Conversation mode (back and forth)")
        console.print("  [cyan]q[/cyan]  Quit")

        choice = input("\n> ").strip()

        if choice == 'q':
            console.print("[yellow]Goodbye![/yellow]")
            break

        elif choice == '1':
            console.print("\n[bold]Available languages:[/bold]")
            for key, lang in LANGUAGES.items():
                console.print(f"  [cyan]{key}[/cyan]  {lang['name']}")
            src = input("From: ").strip()
            tgt = input("To:   ").strip()
            if src in LANGUAGES and tgt in LANGUAGES:
                text = input("Text: ").strip()
                result = pipeline.translate_text(text, src, tgt)
                console.print(f"\n[bold green]Translation: {result}[/bold green]")
                pipeline.tts.speak(result)

        elif choice == '2':
            console.print("\n[bold]Available languages:[/bold]")
            for key, lang in LANGUAGES.items():
                console.print(f"  [cyan]{key}[/cyan]  {lang['name']}")
            src = input("Speak in: ").strip()
            tgt = input("Translate to: ").strip()
            if src in LANGUAGES and tgt in LANGUAGES:
                console.print("\nPress ENTER to start recording...")
                input()
                audio_path = record_until_enter()
                if audio_path:
                    result = pipeline.translate_audio(audio_path, src, tgt)
                    os.unlink(audio_path)

        elif choice == '3':
            conversation_loop(pipeline)


if __name__ == "__main__":
    main()
