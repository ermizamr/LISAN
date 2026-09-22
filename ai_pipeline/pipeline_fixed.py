"""
Ethiopian Language Translator - AI Pipeline
==========================================
Pipeline: Voice Input → Whisper STT → NLLB-200 Translation → Piper TTS → Audio Output

Supported languages:
  - Amharic  (amh_Ethi)
  - English  (eng_Latn)
  - Oromo    (orm_Latn)
  - Somali   (som_Latn)
  - Tigrinya (tir_Ethi)
"""

import os
import time
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
from rich.console import Console
from rich.panel import Panel

console = Console()

# ──────────────────────────────────────────────
# Language Configuration
# ──────────────────────────────────────────────
LANGUAGES = {
    "amh": {
        "name": "Amharic",
        "native": "አማርኛ",
        "nllb_code": "amh_Ethi",
        "whisper_code": "am",
        "flag": "🇪🇹",
    },
    "eng": {
        "name": "English",
        "native": "English",
        "nllb_code": "eng_Latn",
        "whisper_code": "en",
        "flag": "🌐",
    },
    "orm": {
        "name": "Afaan Oromo",
        "native": "Afaan Oromoo",
        "nllb_code": "orm_Latn",
        "whisper_code": "om",
        "flag": "🇪🇹",
    },
    "som": {
        "name": "Somali",
        "native": "Af Soomaali",
        "nllb_code": "som_Latn",
        "whisper_code": "so",
        "flag": "🇸🇴",
    },
    "tir": {
        "name": "Tigrinya",
        "native": "ትግርኛ",
        "nllb_code": "tir_Ethi",
        "whisper_code": None,  # Whisper uses am as fallback
        "flag": "🇪🇷",
    },
}


# ──────────────────────────────────────────────
# STT: Whisper
# ──────────────────────────────────────────────
class WhisperSTT:
    """Speech-to-Text using OpenAI Whisper."""

    def __init__(self, model_size: str = "tiny"):
        self.model_size = model_size
        self.model = None

    def load(self):
        import whisper
        console.print(f"[cyan]Loading Whisper {self.model_size}...[/cyan]")
        self.model = whisper.load_model(self.model_size)
        console.print(f"[green]✓ Whisper {self.model_size} loaded[/green]")

    def transcribe(self, audio_path: str, language_code: str) -> str:
        """Transcribe audio file to text."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        result = self.model.transcribe(
            audio_path,
            language=language_code,
            fp16=False,  # CPU-safe
        )
        return result["text"].strip()

    def record_audio(self, duration: int = 5, sample_rate: int = 16000) -> str:
        """Record audio from microphone and save to temp file."""
        console.print(f"[yellow]🎙️  Recording for {duration} seconds...[/yellow]")
        audio_data = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        console.print("[green]✓ Recording done[/green]")

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio_data, sample_rate)
        return tmp.name


# ──────────────────────────────────────────────
# Translation: NLLB-200
# ──────────────────────────────────────────────
class NLLB200Translator:
    """Neural Machine Translation using Meta NLLB-200."""

    MODEL_NAME = "facebook/nllb-200-distilled-600M"

    def __init__(self):
        self.model = None
        self.tokenizer = None

    def load(self):
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        console.print(f"[cyan]Loading NLLB-200 (600M)... (first run downloads ~2.4GB)[/cyan]")
        self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.MODEL_NAME)
        console.print("[green]✓ NLLB-200 loaded[/green]")

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate text between languages using NLLB lang codes."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        self.tokenizer.src_lang = src_lang
        inputs = self.tokenizer(text, return_tensors="pt", padding=True)

        target_lang_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)
        outputs = self.model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,
            max_length=512,
            num_beams=4,
        )
        translated = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return translated[0]


# ──────────────────────────────────────────────
# TTS: pyttsx3 (offline, cross-platform)
# ──────────────────────────────────────────────
class SimpleTTS:
    """Text-to-Speech using pyttsx3 (works offline, cross-platform)."""

    def __init__(self):
        self.engine = None

    def load(self):
        import pyttsx3
        console.print("[cyan]Loading TTS engine...[/cyan]")
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 150)
        console.print("[green]✓ TTS engine loaded[/green]")

    def speak(self, text: str):
        """Speak text aloud."""
        if self.engine is None:
            raise RuntimeError("Engine not loaded. Call load() first.")
        self.engine.say(text)
        self.engine.runAndWait()

    def save(self, text: str, output_path: str):
        """Save speech to audio file."""
        if self.engine is None:
            raise RuntimeError("Engine not loaded. Call load() first.")
        self.engine.save_to_file(text, output_path)
        self.engine.runAndWait()


# ──────────────────────────────────────────────
# Full Pipeline
# ──────────────────────────────────────────────
class TranslatorPipeline:
    """
    End-to-end translation pipeline:
    Audio → STT → Translation → TTS → Audio
    """

    def __init__(self, whisper_size: str = "tiny"):
        self.stt = WhisperSTT(model_size=whisper_size)
        self.translator = NLLB200Translator()
        self.tts = SimpleTTS()
        self._loaded = False

    def load_all(self):
        """Load all models into memory."""
        console.print(Panel("[bold cyan]Loading Ethiopian Translator AI Pipeline[/bold cyan]"))
        self.stt.load()
        self.translator.load()
        self.tts.load()
        self._loaded = True
        console.print(Panel("[bold green]✅ All models loaded! Pipeline ready.[/bold green]"))

    def translate_text(self, text: str, src_lang_key: str, tgt_lang_key: str) -> str:
        """Translate text between two languages."""
        src = LANGUAGES[src_lang_key]["nllb_code"]
        tgt = LANGUAGES[tgt_lang_key]["nllb_code"]
        return self.translator.translate(text, src, tgt)

    def translate_audio(
        self,
        audio_path: str,
        src_lang_key: str,
        tgt_lang_key: str,
        speak_result: bool = True,
    ) -> dict:
        """Full pipeline: audio file → translated text → (optionally speak)."""
        src_lang = LANGUAGES[src_lang_key]
        tgt_lang = LANGUAGES[tgt_lang_key]

        console.print(f"\n[bold]Pipeline: {src_lang['flag']} {src_lang['name']} → {tgt_lang['flag']} {tgt_lang['name']}[/bold]")

        # Step 1: STT
        t0 = time.time()
        whisper_lang = src_lang["whisper_code"] or "am"
        console.print("[cyan]Step 1: Transcribing speech...[/cyan]")
        transcribed = self.stt.transcribe(audio_path, whisper_lang)
        stt_time = time.time() - t0
        console.print(f"[green]  ✓ Transcribed ({stt_time:.1f}s): '{transcribed}'[/green]")

        # Step 2: Translation
        t1 = time.time()
        console.print("[cyan]Step 2: Translating...[/cyan]")
        translated = self.translate_text(transcribed, src_lang_key, tgt_lang_key)
        trans_time = time.time() - t1
        console.print(f"[green]  ✓ Translated ({trans_time:.1f}s): '{translated}'[/green]")

        # Step 3: TTS
        if speak_result:
            t2 = time.time()
            console.print("[cyan]Step 3: Speaking translation...[/cyan]")
            self.tts.speak(translated)
            tts_time = time.time() - t2
            console.print(f"[green]  ✓ Spoken ({tts_time:.1f}s)[/green]")

        total_time = time.time() - t0
        console.print(f"\n[bold green]⚡ Total latency: {total_time:.1f}s[/bold green]")

        return {
            "source_text": transcribed,
            "translated_text": translated,
            "src_lang": src_lang_key,
            "tgt_lang": tgt_lang_key,
            "latency_stt": stt_time,
            "latency_translation": trans_time,
            "total_latency": total_time,
        }

    def live_translate(self, src_lang_key: str, tgt_lang_key: str, duration: int = 5):
        """Record from mic and translate in real-time."""
        audio_path = self.stt.record_audio(duration=duration)
        result = self.translate_audio(audio_path, src_lang_key, tgt_lang_key)
        os.unlink(audio_path)  # cleanup
        return result


# ──────────────────────────────────────────────
# Interactive Demo CLI
# ──────────────────────────────────────────────
def print_language_menu():
    console.print("\n[bold]Available Languages:[/bold]")
    for key, lang in LANGUAGES.items():
        console.print(f"  [cyan]{key}[/cyan] → {lang['flag']} {lang['name']} ({lang['native']})")


def run_demo():
    console.print(Panel(
        "[bold yellow]🌍 Ethiopian Language Translator[/bold yellow]\n"
        "[dim]Offline-capable · Real-time · Multi-language[/dim]",
        expand=False
    ))

    pipeline = TranslatorPipeline(whisper_size="tiny")
    pipeline.load_all()

    while True:
        console.print("\n" + "─" * 50)
        console.print("[bold]Choose mode:[/bold]")
        console.print("  [cyan]1[/cyan] → Text translation (type input)")
        console.print("  [cyan]2[/cyan] → Voice translation (mic input)")
        console.print("  [cyan]q[/cyan] → Quit")

        choice = input("\n> ").strip()

        if choice == "q":
            console.print("[yellow]Goodbye! / ቻው! / Nagaatti![/yellow]")
            break

        print_language_menu()
        src = input("\nSource language code: ").strip()
        tgt = input("Target language code: ").strip()

        if src not in LANGUAGES or tgt not in LANGUAGES:
            console.print("[red]Invalid language code. Try again.[/red]")
            continue

        if choice == "1":
            text = input(f"\nEnter text in {LANGUAGES[src]['name']}: ").strip()
            result = pipeline.translate_text(text, src, tgt)
            console.print(f"\n[bold green]Translation:[/bold green] {result}")
            pipeline.tts.speak(result)

        elif choice == "2":
            secs = input("Recording duration in seconds (default 5): ").strip()
            duration = int(secs) if secs.isdigit() else 5
            result = pipeline.live_translate(src, tgt, duration=duration)
            console.print(f"\n[bold]Result:[/bold]")
            console.print(f"  Source    : {result['source_text']}")
            console.print(f"  Translated: [bold green]{result['translated_text']}[/bold green]")


if __name__ == "__main__":
    run_demo()
