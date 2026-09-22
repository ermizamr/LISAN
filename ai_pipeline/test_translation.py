"""
Quick test: Amharic <-> English translation (text only, no audio required)
Run this first to verify the translation model works before testing voice.
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from pipeline import NLLB200Translator, SimpleTTS, LANGUAGES
from rich.console import Console
from rich.table import Table

console = Console(force_terminal=True, highlight=False)

def test_translation():
    console.print("\n[bold cyan]Testing Translation Pipeline (Text Only)[/bold cyan]\n")

    translator = NLLB200Translator()
    translator.load()

    tts = SimpleTTS()
    tts.load()

    # Test pairs
    test_cases = [
        ("Hello, how are you?",       "eng", "amh"),
        ("ሰላም, እንዴት ነህ?",              "amh", "eng"),
        ("Where is the hospital?",     "eng", "orm"),
        ("Galatoomaa, nagaatti!",      "orm", "eng"),
        ("I need a doctor.",           "eng", "amh"),
        ("ውሃ ይፈልጋሉ?",                 "amh", "eng"),
    ]

    table = Table(title="Translation Test Results", show_lines=True)
    table.add_column("Source Text", style="cyan", max_width=30)
    table.add_column("From → To", style="yellow")
    table.add_column("Translation", style="green", max_width=30)

    for text, src, tgt in test_cases:
        src_lang = LANGUAGES[src]
        tgt_lang = LANGUAGES[tgt]
        result = translator.translate(
            text,
            src_lang["nllb_code"],
            tgt_lang["nllb_code"]
        )
        table.add_row(
            text,
            f"{src_lang['flag']} {src_lang['name']} → {tgt_lang['flag']} {tgt_lang['name']}",
            result
        )
        console.print(f"[dim]✓ {text[:25]}...[/dim]")

    console.print(table)

    # Speak one result
    console.print("\n[yellow]Speaking last translation...[/yellow]")
    last_result = translator.translate("Welcome to Ethiopia!", "eng_Latn", "amh_Ethi")
    console.print(f"[green]'Welcome to Ethiopia!' in Amharic: {last_result}[/green]")
    tts.speak(last_result)

    console.print("\n[bold green]✅ Translation test complete![/bold green]")


if __name__ == "__main__":
    test_translation()
