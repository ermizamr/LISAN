"""
Ethiopian Language Translator - AI Pipeline
==========================================
Pipeline: Voice Input -> Whisper STT -> NLLB-200 Translation -> Piper TTS -> Audio Output

Supported languages:
  - Amharic  (amh_Ethi)
  - English  (eng_Latn)
  - Oromo    (orm_Latn)
  - Somali   (som_Latn)
  - Tigrinya (tir_Ethi)
"""

import os
os.environ["MKL_DISABLE_FAST_MM"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
import sys
import time
import tempfile
import numpy as np
try:
    import sounddevice as sd
except Exception:
    sd = None
import soundfile as sf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.panel import Panel

console = Console(highlight=False, force_terminal=False)

# ──────────────────────────────────────────────
# Language Configuration
# ──────────────────────────────────────────────
LANGUAGES = {
    "amh": {
        "name": "Amharic",
        "native": "አማርኛ",
        "nllb_code": "amh_Ethi",
        "whisper_code": "am",
        "stt_model": "amharic",   # use dedicated AmharicSTT
        "flag": "🇪🇹",
    },
    "eng": {
        "name": "English",
        "native": "English",
        "nllb_code": "eng_Latn",
        "whisper_code": "en",
        "stt_model": "whisper",   # Whisper is best for English
        "flag": "🌐",
    },
    "orm": {
        "name": "Afaan Oromo",
        "native": "Afaan Oromoo",
        "nllb_code": "gaz_Latn",
        "whisper_code": "om",
        "stt_model": "ethio_multilingual",    # badrex/Ethio-ASR-multilingual-600M
        "flag": "ET",
    },
    "som": {
        "name": "Somali",
        "native": "Af Soomaali",
        "nllb_code": "som_Latn",
        "whisper_code": "so",
        "stt_model": "whisper",  # Whisper handles Somali
        "flag": "🇸🇴",
    },
    "tir": {
        "name": "Tigrinya",
        "native": "ትግርኛ",
        "nllb_code": "tir_Ethi",
        "whisper_code": "ti",
        "stt_model": "ethio_multilingual", # badrex/Ethio-ASR-multilingual-600M
        "flag": "🇪🇷",
    },
}


# ──────────────────────────────────────────────
# STT: Amharic-specific (badrex/Ethio-ASR-amharic)
# Wav2Vec2Bert fine-tuned on dataset.et Amharic speech
# 354 Amharic characters in vocab — far more accurate than Whisper for Amharic
# ──────────────────────────────────────────────
class AmharicSTT:
    """Dedicated Amharic Speech-to-Text using badrex/Ethio-ASR-amharic.

    This model was fine-tuned specifically on Ethiopian Amharic speech data
    from dataset.et, giving much better accuracy than generic Whisper tiny.
    Architecture: Wav2Vec2Bert (24 encoder layers, 354-char Ethiopic vocab).
    Also used for Tigrinya (same Ethiopic script family).
    """

    MODEL_NAME = "badrex/Ethio-ASR-amharic"

    def __init__(self):
        self.processor = None
        self.model = None

    def load(self):
        from transformers import Wav2Vec2BertForCTC, AutoProcessor
        console.print("[cyan]Loading Amharic ASR (dataset.et model)...[/cyan]")
        self.processor = AutoProcessor.from_pretrained(self.MODEL_NAME)
        self.model = Wav2Vec2BertForCTC.from_pretrained(self.MODEL_NAME)
        self.model.eval()
        console.print("[green]✓ Amharic ASR loaded[/green]")

    def transcribe(self, audio_path: str, _language_code: str = "am") -> str:
        """Transcribe Amharic/Tigrinya speech from a WAV file."""
        import torch
        import soundfile as sf
        import scipy.signal as sig

        if self.model is None:
            raise RuntimeError("AmharicSTT not loaded. Call load() first.")

        audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sample_rate != 16000:
            num_samples = int(len(audio) * 16000 / sample_rate)
            audio = sig.resample(audio, num_samples).astype(np.float32)

        inputs = self.processor(
            audio, sampling_rate=16000, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        return self.processor.batch_decode(predicted_ids)[0].strip()


# ──────────────────────────────────────────────────────────────────
# STT: Ethiopian Multilingual (badrex/Ethio-ASR-multilingual-600M)
# ONE model for Amharic + Oromo + Tigrinya — saves ~4.8GB RAM
# vs loading 3 separate 606M models
# ──────────────────────────────────────────────────────────────────
class EthioMultilingualSTT:
    """Single Wav2Vec2Bert model covering Amharic, Oromo, and Tigrinya.

    Uses badrex/Ethio-ASR-multilingual-600M — same 606M architecture
    as the language-specific models but trained across all Ethiopian
    languages (WAXAL / Dataset.ET). One load, three languages, ~2.4GB RAM.

    Language codes: 'am' (Amharic), 'om' (Oromo), 'ti' (Tigrinya)
    """

    MODEL_NAME = "badrex/Ethio-ASR-multilingual-600M"

    def __init__(self):
        self.processor = None
        self.model = None

    def try_load(self) -> bool:
        """Attempt to load Ethio-ASR multilingual model from local cache."""
        if self.model is not None and self.processor is not None:
            return True

        from transformers import Wav2Vec2BertForCTC, AutoProcessor
        import os
        from pathlib import Path

        # Dynamically locate cached snapshot from Hugging Face hub
        snapshot_dir = None
        hub_root = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub" / "models--badrex--Ethio-ASR-multilingual-600M" / "snapshots"
        if hub_root.exists():
            snapshots = sorted(hub_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
            for s in snapshots:
                if (s / "model.safetensors").exists() and (s / "model.safetensors").stat().st_size > 2_000_000_000:
                    snapshot_dir = str(s)
                    break

        load_path = snapshot_dir if snapshot_dir else self.MODEL_NAME
        is_local = bool(snapshot_dir)

        console.print(f"[cyan]Loading Ethiopian Multilingual ASR ({load_path})...[/cyan]")
        try:
            import gc, torch
            gc.collect()
            self.processor = AutoProcessor.from_pretrained(load_path, local_files_only=is_local)
            self.model = Wav2Vec2BertForCTC.from_pretrained(
                load_path,
                local_files_only=is_local,
                torch_dtype=torch.float32,
            )
            self.model.eval()
            self._build_lexicon_decoders()
            console.print("[green]✓ Ethiopian Multilingual ASR loaded (Amharic · Afaan Oromo · Tigrinya)[/green]")
            return True
        except Exception as error:
            console.print(f"[yellow]EthioMultilingualSTT load failed: {error}[/yellow]")
            return False

    def _build_lexicon_decoders(self):
        """Build separate, language-isolated beam search decoders to prevent cross-language search bloat."""
        try:
            from pyctcdecode import build_ctcdecoder
            from pathlib import Path
            import re

            lexicon_dir = Path(__file__).resolve().parent.parent / "data" / "lexicon"
            self.decoders = {}

            vocab = self.processor.tokenizer.get_vocab()
            inv = {idx: tok for tok, idx in vocab.items()}
            labels = [inv[i] for i in range(len(vocab))]

            lang_files = {
                "om": "orm_unigrams.txt",
                "am": "amh_unigrams.txt",
                "ti": "tir_unigrams.txt",
            }

            for lang_key, fname in lang_files.items():
                p = lexicon_dir / fname
                if p.exists():
                    # Read unigrams, normalizing hudhaa quotes for Qubee
                    unigrams = [re.sub(r"[’‘`´ʻʼ]", "'", w.strip().lower()) for w in p.read_text(encoding="utf-8").splitlines() if w.strip()]
                    if unigrams:
                        self.decoders[lang_key] = build_ctcdecoder(labels, unigrams=unigrams)
                        console.print(f"[green]✓ EthioMultilingualSTT dedicated '{lang_key}' beam decoder enabled ({len(unigrams):,} unigrams)[/green]")

            # Fallback default
            self.decoder = self.decoders.get("am") or (list(self.decoders.values())[0] if self.decoders else None)
        except Exception as e:
            console.print(f"[yellow]Lexicon decoder note: {e}[/yellow]")
            self.decoders = {}
            self.decoder = None

    def score_language_logits(self, logits: np.ndarray) -> tuple[dict[str, float], dict[str, str]]:
        """Score one CTC emission with each available language decoder."""
        scores: dict[str, float] = {}
        texts: dict[str, str] = {}
        for language_code, decoder in getattr(self, "decoders", {}).items():
            try:
                beams = decoder.decode_beams(logits, beam_width=50)
                if beams:
                    texts[language_code] = beams[0][0].strip()
                    scores[language_code] = float(beams[0][4])
            except Exception as error:
                console.print(f"[yellow]CTC {language_code} scoring warning: {error}[/yellow]")
        return scores, texts

    def load(self):
        self.try_load()

    def transcribe(self, audio_path: str, language_code: str = "am") -> str:
        """Transcribe speech. language_code: 'am', 'om', or 'ti'."""
        import torch
        import soundfile as sf
        import scipy.signal as sig
        import re

        if self.model is None or self.processor is None:
            if not self.try_load():
                raise RuntimeError("EthioMultilingualSTT not loaded. Weights missing from local cache.")

        audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sample_rate != 16000:
            num_samples = int(len(audio) * 16000 / sample_rate)
            audio = sig.resample(audio, num_samples).astype(np.float32)

        audio = WhisperSTT._trim_silence(audio, 16000)
        if audio.size == 0:
            return ""

        inputs = self.processor(
            audio, sampling_rate=16000, return_tensors="pt", padding=True
        )

        with torch.no_grad():
            logits = self.model(**inputs).logits

        # Route strictly to language-isolated decoder to eliminate cross-language / cross-script confusion
        norm_lang = "om" if language_code in ("om", "orm", "gaz_Latn") else ("ti" if language_code in ("ti", "tir", "tir_Ethi") else "am")
        selected_decoder = getattr(self, "decoders", {}).get(norm_lang) or getattr(self, "decoder", None)

        if selected_decoder is not None:
            try:
                raw_text = selected_decoder.decode(logits[0].float().cpu().numpy()).strip()
            except Exception:
                predicted_ids = torch.argmax(logits, dim=-1)
                raw_text = self.processor.batch_decode(predicted_ids)[0].strip()
        else:
            predicted_ids = torch.argmax(logits, dim=-1)
            raw_text = self.processor.batch_decode(predicted_ids)[0].strip()

        # Strip language token prefixes like [AMH], [ORM], [TIR], [SID], [WAL]
        raw_text = re.sub(r"^\[[A-Za-z]+\]\s*", "", raw_text).strip()
        if norm_lang == "om":
            raw_text = re.sub(r"[’‘`´ʻʼ]", "'", raw_text)
        return raw_text



# ──────────────────────────────────────────────
# STT: Oromo-specific (badrex/Ethio-ASR-oromo)
# (kept for optional use — pipeline uses multilingual by default)
# ──────────────────────────────────────────────
class OromoSTT:
    """Dedicated Afaan Oromo ASR using badrex/Ethio-ASR-oromo.
    Wav2Vec2Bert fine-tuned specifically on Oromo speech data.
    """

    MODEL_NAME = "badrex/Ethio-ASR-oromo"

    def __init__(self):
        self.processor = None
        self.model = None

    def load(self):
        from transformers import Wav2Vec2BertForCTC, AutoProcessor
        console.print("[cyan]Loading Oromo ASR model...[/cyan]")
        self.processor = AutoProcessor.from_pretrained(self.MODEL_NAME)
        self.model = Wav2Vec2BertForCTC.from_pretrained(self.MODEL_NAME)
        self.model.eval()
        console.print("[green]✓ Oromo ASR loaded[/green]")

    def transcribe(self, audio_path: str, _language_code: str = "om") -> str:
        """Transcribe Oromo speech from a WAV file."""
        import torch
        import soundfile as sf
        import scipy.signal as sig

        if self.model is None:
            raise RuntimeError("OromoSTT not loaded. Call load() first.")

        audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sample_rate != 16000:
            num_samples = int(len(audio) * 16000 / sample_rate)
            audio = sig.resample(audio, num_samples).astype(np.float32)

        inputs = self.processor(
            audio, sampling_rate=16000, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        return self.processor.batch_decode(predicted_ids)[0].strip()


# ──────────────────────────────────────────────
# STT: Tigrinya-specific (badrex/Ethio-ASR-tigrinya)
# ──────────────────────────────────────────────
class TigrinyaSTT:
    """Dedicated Tigrinya ASR using badrex/Ethio-ASR-tigrinya.
    Wav2Vec2Bert fine-tuned specifically on Tigrinya speech data.
    """

    MODEL_NAME = "badrex/Ethio-ASR-tigrinya"

    def __init__(self):
        self.processor = None
        self.model = None

    def load(self):
        from transformers import Wav2Vec2BertForCTC, AutoProcessor
        console.print("[cyan]Loading Tigrinya ASR model...[/cyan]")
        self.processor = AutoProcessor.from_pretrained(self.MODEL_NAME)
        self.model = Wav2Vec2BertForCTC.from_pretrained(self.MODEL_NAME)
        self.model.eval()
        console.print("[green]✓ Tigrinya ASR loaded[/green]")

    def transcribe(self, audio_path: str, _language_code: str = "ti") -> str:
        """Transcribe Tigrinya speech from a WAV file."""
        import torch
        import soundfile as sf
        import scipy.signal as sig

        if self.model is None:
            raise RuntimeError("TigrinyaSTT not loaded. Call load() first.")

        audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sample_rate != 16000:
            num_samples = int(len(audio) * 16000 / sample_rate)
            audio = sig.resample(audio, num_samples).astype(np.float32)

        inputs = self.processor(
            audio, sampling_rate=16000, return_tensors="pt", padding=True
        )
        with torch.no_grad():
            logits = self.model(**inputs).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        return self.processor.batch_decode(predicted_ids)[0].strip()


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
        """Transcribe audio file to text.
        Loads audio via soundfile (no FFmpeg needed) and passes
        a numpy float32 array directly to Whisper.
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Load audio ourselves — bypass Whisper's FFmpeg-dependent load_audio
        import soundfile as sf
        import numpy as np
        audio_data, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)

        # Mix down to mono if stereo
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)

        # Resample to 16kHz if needed (Whisper requirement)
        if sample_rate != 16000:
            import scipy.signal as sig
            num_samples = int(len(audio_data) * 16000 / sample_rate)
            audio_data = sig.resample(audio_data, num_samples)

        audio_data = self._trim_silence(audio_data, 16000)
        if audio_data.size == 0:
            return ""

        initial_prompt = "አማርኛ ንግግር።" if language_code == "am" else None

        result = self.model.transcribe(
            audio_data,          # numpy array, not file path
            language=language_code,
            fp16=False,          # CPU-safe
            task="transcribe",
            temperature=0,
            condition_on_previous_text=False,
            compression_ratio_threshold=2.2,
            logprob_threshold=-0.8,
            no_speech_threshold=0.45,
            initial_prompt=initial_prompt,
        )
        
        # Guard against Whisper silence hallucinations on background noise
        segments = result.get("segments", [])
        if segments:
            valid_segments = []
            for seg in segments:
                no_speech_p = seg.get("no_speech_prob", 0.0)
                avg_lp = seg.get("avg_logprob", 0.0)
                seg_text = seg.get("text", "").strip()
                if not seg_text:
                    continue
                # If segment has high no_speech_prob or critically low logprob, reject it as hallucination
                if no_speech_p > 0.55 or avg_lp < -1.15:
                    continue
                valid_segments.append(seg_text)
            return " ".join(valid_segments).strip()

        return result.get("text", "").strip()

    @staticmethod
    def _trim_silence(audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """Remove quiet padding and reject pure noise to prevent Whisper from hallucinating."""
        if audio_data.size == 0:
            return audio_data

        peak = float(np.max(np.abs(audio_data)))
        # Any signal below 0.02 peak (-34 dB) in standard phone mic audio is room noise/silence
        if peak < 0.02:
            return np.array([], dtype=np.float32)

        window_size = max(1, int(sample_rate * 0.02))
        energy = np.convolve(
            np.abs(audio_data),
            np.ones(window_size, dtype=np.float32) / window_size,
            mode="same",
        )
        active = np.flatnonzero(energy >= max(0.012, peak * 0.06))
        if active.size == 0:
            return np.array([], dtype=np.float32)

        start_padding = int(sample_rate * 0.15)
        end_padding = int(sample_rate * 0.30)
        start = max(0, int(active[0]) - start_padding)
        end = min(audio_data.size, int(active[-1]) + end_padding)
        trimmed = audio_data[start:end].astype(np.float32, copy=False)

        # Phone microphones vary in sensitivity. Stabilize quiet speech without amplifying floor hiss.
        trimmed_peak = float(np.max(np.abs(trimmed)))
        if 0.035 <= trimmed_peak < 0.7:
            gain = min(3.0, 0.75 / trimmed_peak)
            trimmed = trimmed * gain
            trimmed = np.clip(trimmed, -1.0, 1.0)
        elif trimmed_peak < 0.03:
            return np.array([], dtype=np.float32)
        return trimmed

    def record_audio(self, duration: int = 5, sample_rate: int = 16000) -> str:
        """Record audio from microphone and save to temp file."""
        if sd is None:
            raise RuntimeError("Live microphone recording is not supported in headless environments (sounddevice/PortAudio missing). Use file audio inputs.")
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


class DatasetEtHoheSTT:
    """Official Dataset.ET Hohe ASR (Amharic Speech-to-Text).

    Model: snapwre/hohe-asr-amharic
    Trained on 880 hours of Amharic speech across 5 regional dialects.
    Achieves 16.1% WER with language model. Single-pass Conformer/Wav2Vec2Bert.
    """

    MODEL_NAME = "snapwre/hohe-asr-amharic"

    def __init__(self):
        self.processor = None
        self.model = None
        self.decoder = None

    def load(self):
        """Initial check for Dataset.ET Hohe ASR weights."""
        if not self.try_load():
            console.print(f"[yellow]Dataset.ET Hohe weights still downloading in background. EthioMultilingualSTT will handle Amharic speech until ready.[/yellow]")

    def try_load(self) -> bool:
        """Attempt to load Hohe ASR if files are locally available."""
        if self.model is not None and self.processor is not None:
            return True

        from transformers import AutoModelForCTC, AutoProcessor
        import os
        from pathlib import Path

        # Dynamically locate cached snapshot from Hugging Face hub
        snapshot_dir = None
        hub_root = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub" / "models--snapwre--hohe-asr-amharic" / "snapshots"
        if hub_root.exists():
            snapshots = sorted(hub_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
            for s in snapshots:
                if (s / "model.safetensors").exists() and (s / "model.safetensors").stat().st_size > 2_000_000_000:
                    snapshot_dir = str(s)
                    break

        load_path = snapshot_dir if snapshot_dir else self.MODEL_NAME
        is_local = bool(snapshot_dir)

        console.print(f"[cyan]Loading Dataset.ET Hohe ASR ({load_path})...[/cyan]")
        try:
            import gc
            gc.collect()
            import torch
            self.processor = AutoProcessor.from_pretrained(load_path, local_files_only=is_local)
            self.model = AutoModelForCTC.from_pretrained(
                load_path,
                local_files_only=is_local,
                torch_dtype=torch.float32,
            )
            self.model.eval()
            self._load_decoder()
            console.print("[green]✓ Dataset.ET Hohe Amharic ASR loaded successfully (native float32 fast mode)![/green]")
            return True
        except Exception as error:
            console.print(f"[yellow]Dataset.ET Hohe load failed: {error}[/yellow]")
            return False

    def _load_decoder(self):
        try:
            from pyctcdecode import build_ctcdecoder
            import json
            from huggingface_hub import hf_hub_download

            decoder_cfg_path = hf_hub_download(self.MODEL_NAME, "lm/decoder.json", local_files_only=True)
            lm_path = hf_hub_download(self.MODEL_NAME, "lm/am-5gram.bin", local_files_only=True)
            cfg = json.load(open(decoder_cfg_path))
            vocab = self.processor.tokenizer.get_vocab()
            labels = [""] * (max(vocab.values()) + 1)
            for tok, i in vocab.items():
                labels[i] = " " if tok == "|" else ("" if i == self.processor.tokenizer.pad_token_id else tok)

            try:
                self.decoder = build_ctcdecoder(labels, lm_path, alpha=cfg.get("alpha", 0.5), beta=cfg.get("beta", 1.5))
                self.has_lm = True
                console.print("[green]✓ Dataset.ET Hohe 5-gram LM decoder enabled[/green]")
            except Exception:
                self.decoder = None
                self.has_lm = False
                console.print("[green]✓ Dataset.ET Hohe native CTC greedy decoder enabled[/green]")
        except Exception as e:
            console.print(f"[yellow]CTC decoder initialization note: {e}[/yellow]")
            self.decoder = None
            self.has_lm = False

    def transcribe(self, audio_path: str) -> str:
        import torch
        import soundfile as sf
        import scipy.signal as sig
        import re

        if self.model is None or self.processor is None:
            raise RuntimeError("Dataset.ET Hohe ASR not loaded. Call load() first.")

        audio_data, sample_rate = sf.read(
            audio_path,
            dtype="float32",
            always_2d=False,
        )
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)
        if sample_rate != 16000:
            num_samples = int(len(audio_data) * 16000 / sample_rate)
            audio_data = sig.resample(audio_data, num_samples).astype(np.float32)

        audio_data = WhisperSTT._trim_silence(audio_data, 16000)
        if audio_data.size == 0:
            return ""

        inputs = self.processor(
            audio_data,
            sampling_rate=16000,
            return_tensors="pt",
            padding=True,
        )
        model_dtype = getattr(self.model, "dtype", torch.float32)
        inputs = {
            k: v.to(model_dtype) if torch.is_floating_point(v) else v
            for k, v in inputs.items()
        }
        with torch.inference_mode():
            logits = self.model(**inputs).logits

        if getattr(self, "has_lm", False) and self.decoder is not None:
            raw_text = self.decoder.decode(logits[0].float().cpu().numpy()).strip()
        else:
            predicted_ids = torch.argmax(logits, dim=-1)
            raw_text = self.processor.batch_decode(predicted_ids)[0].strip()

        # Strip [AMH] prefix tag per Dataset.ET documentation
        clean_text = re.sub(r"^\[AMH\]\s*", "", raw_text, flags=re.IGNORECASE).strip()
        return clean_text


# ──────────────────────────────────────────────
# Translation: NLLB-200 (CTranslate2 INT8 with PyTorch fallback)
# ──────────────────────────────────────────────
class NLLB200Translator:
    """Neural Machine Translation using Meta NLLB-200.
    
    Prefers CTranslate2 INT8 quantized model for ~4x faster inference
    and 4x lower RAM (~600MB vs ~2.4GB).
    Falls back gracefully to PyTorch transformers if needed.
    """

    MODEL_NAME = "facebook/nllb-200-distilled-600M"
    OPTIMIZED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models_optimized", "nllb_int8")

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.ct2_translator = None

    def load(self):
        from transformers import AutoTokenizer

        console.print(f"[cyan]Loading NLLB-200 tokenizer...[/cyan]")
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME, local_files_only=True)
        except Exception:
            self.tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)


        # Check for CTranslate2 INT8 model first
        if os.path.isdir(self.OPTIMIZED_DIR) and os.path.isfile(os.path.join(self.OPTIMIZED_DIR, "model.bin")):
            try:
                import gc
                gc.collect()
                import ctranslate2
                console.print(f"[cyan]Loading CTranslate2 INT8 engine (fast CPU mode)...[/cyan]")
                self.ct2_translator = ctranslate2.Translator(
                    self.OPTIMIZED_DIR,
                    device="cpu",
                    compute_type="int8",
                    intra_threads=1,
                    inter_threads=1,
                )
                console.print("[green]✓ NLLB-200 CTranslate2 INT8 loaded (ultra-fast 0.25s translation, ~600MB RAM)[/green]")
                return
            except Exception as e:
                console.print(f"[yellow]CTranslate2 load failed ({e}), falling back to PyTorch...[/yellow]")

        # PyTorch fallback
        from transformers import AutoModelForSeq2SeqLM
        console.print(f"[cyan]Loading NLLB-200 via PyTorch (600M)...[/cyan]")
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.MODEL_NAME)
        console.print("[cyan]Warming up translation engine...[/cyan]")
        self.tokenizer.src_lang = "eng_Latn"
        _inputs = self.tokenizer("hello", return_tensors="pt")
        _tgt = self.tokenizer.convert_tokens_to_ids("amh_Ethi")
        self.model.generate(**_inputs, forced_bos_token_id=_tgt, max_length=32, num_beams=1)
        console.print("[green]✓ NLLB-200 PyTorch loaded and warmed up[/green]")

    def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate text between languages using NLLB lang codes with sentence chunking."""
        if not text or not text.strip():
            return ""

        import re
        # Split on sentence boundaries: punctuation followed by space (., ?, !, ।, ፧, ።)
        raw_sentences = [s.strip() for s in re.split(r'(?<=[.?!።፧])\s+', text.strip()) if s.strip()]
        if not raw_sentences:
            raw_sentences = [text.strip()]

        # CTranslate2 path
        if self.ct2_translator is not None:
            self.tokenizer.src_lang = src_lang
            batch_tokens = []
            target_prefixes = []
            for sent in raw_sentences:
                toks = self.tokenizer.convert_ids_to_tokens(self.tokenizer.encode(sent))
                batch_tokens.append(toks)
                target_prefixes.append([tgt_lang])
            import math
            results = self.ct2_translator.translate_batch(
                batch_tokens,
                target_prefix=target_prefixes,
                beam_size=4,
                repetition_penalty=1.25,
                no_repeat_ngram_size=3,
                max_decoding_length=512,
                return_scores=True,
            )
            translated_sentences = []
            for sent, res in zip(raw_sentences, results):
                hyp_tokens = res.hypotheses[0][1:]
                score = res.scores[0]
                sent_text = self.tokenizer.decode(self.tokenizer.convert_tokens_to_ids(hyp_tokens), skip_special_tokens=True).strip()

                # In CTranslate2 (length_penalty=1.0), score is ALREADY length-normalized log-probability:
                norm_logprob = score
                norm_prob = math.exp(norm_logprob)

                # Statistical Noise / Attractor Chaff Suppression:
                # If normalized log-prob < -1.15 (token prob < 31.6%) and clause is short (<= 4 words),
                # the hypothesis is mathematically detached from the source (acoustic chaff/hallucination).
                if norm_logprob < -1.15 and len(sent.split()) <= 4:
                    console.print(f"[yellow]⚠ Suppressed ungrounded noise (prob={norm_prob:.2f}, score={score:.2f}): '{sent}' -> '{sent_text}'[/yellow]")
                    continue

                if sent_text:
                    translated_sentences.append(sent_text)

            if not translated_sentences:
                fallback_msg = {
                    "eng_Latn": "[Audio unclear]",
                    "amh_Ethi": "[ድምፁ ግልጽ አይደለም]",
                    "gaz_Latn": "[Sagaleen hin dhagahamne]",
                    "tir_Ethi": "[ድምጺ ንጹር ኣይኮነን]",
                    "som_Latn": "[Codku ma cadda]",
                }.get(tgt_lang, "[Audio unclear]")
                return fallback_msg

            return " ".join(translated_sentences)

        # PyTorch fallback path
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        self.tokenizer.src_lang = src_lang
        inputs = self.tokenizer(text, return_tensors="pt", padding=True)
        target_lang_id = self.tokenizer.convert_tokens_to_ids(tgt_lang)
        outputs = self.model.generate(
            **inputs,
            forced_bos_token_id=target_lang_id,
            max_length=256,
            num_beams=2,
        )
        translated = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return translated[0]


# ──────────────────────────────────────────────
# TTS: Meta MMS-TTS (VITS) Neural Speech Engine
# ──────────────────────────────────────────────
class MMSTTSEngine:
    """
    Offline Text-to-Speech using Meta MMS-TTS (VITS) models.
    Supports native speech synthesis for Ethiopian languages:
      - Afaan Oromoo: facebook/mms-tts-orm
      - Amharic: facebook/mms-tts-amh
      - Tigrinya: facebook/mms-tts-tir
      - Somali: facebook/mms-tts-som
      - English: facebook/mms-tts-eng
    Gracefully falls back to pyttsx3 if MMS model is unavailable.
    """

    MODEL_MAP = {
        "orm": "facebook/mms-tts-orm",
        "om": "facebook/mms-tts-orm",
        "gaz_Latn": "facebook/mms-tts-orm",
        "amh": "facebook/mms-tts-amh",
        "am": "facebook/mms-tts-amh",
        "amh_Ethi": "facebook/mms-tts-amh",
        "tir": "facebook/mms-tts-tir",
        "ti": "facebook/mms-tts-tir",
        "tir_Ethi": "facebook/mms-tts-tir",
        "som": "facebook/mms-tts-som",
        "so": "facebook/mms-tts-som",
        "som_Latn": "facebook/mms-tts-som",
        "eng": "facebook/mms-tts-eng",
        "en": "facebook/mms-tts-eng",
        "eng_Latn": "facebook/mms-tts-eng",
    }

    def __init__(self):
        self._models = {}
        self._tokenizers = {}
        self._pyttsx3_engine = None

    def load(self, preload_langs=("orm", "amh")):
        """Preload common TTS models into cache."""
        console.print("[cyan]Initializing Meta MMS-TTS engine...[/cyan]")
        for lang in preload_langs:
            try:
                self._get_model_and_tokenizer(lang)
            except Exception as e:
                console.print(f"[yellow]MMS-TTS preload note for '{lang}': {e}[/yellow]")
        console.print("[green]✓ Meta MMS-TTS engine initialized (Oromo · Amharic · Tigrinya · Somali · English)[/green]")

    def _get_model_and_tokenizer(self, lang: str):
        norm_lang = (lang or "orm").lower().strip()
        model_name = self.MODEL_MAP.get(norm_lang)
        if not model_name:
            model_name = self.MODEL_MAP["eng"]

        if model_name in self._models and model_name in self._tokenizers:
            return self._models[model_name], self._tokenizers[model_name]

        from transformers import VitsModel, AutoTokenizer
        import torch

        try:
            tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
            model = VitsModel.from_pretrained(model_name, local_files_only=True)
        except Exception:
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = VitsModel.from_pretrained(model_name)
        model.eval()

        self._models[model_name] = model
        self._tokenizers[model_name] = tokenizer
        return model, tokenizer

    def synthesize_to_bytes(self, text: str, lang: str = "orm") -> bytes:
        """Synthesize text to in-memory WAV audio bytes."""
        import io
        import soundfile as sf
        import torch
        import numpy as np

        if not text or not text.strip():
            buf = io.BytesIO()
            sf.write(buf, np.zeros(1600, dtype=np.float32), samplerate=16000, format="WAV")
            return buf.getvalue()

        try:
            model, tokenizer = self._get_model_and_tokenizer(lang)
            inputs = tokenizer(text.strip(), return_tensors="pt")
            with torch.no_grad():
                output = model(**inputs).waveform

            waveform = output[0].cpu().numpy()
            sample_rate = model.config.sampling_rate

            buf = io.BytesIO()
            sf.write(buf, waveform, samplerate=sample_rate, format="WAV")
            return buf.getvalue()
        except Exception as e:
            console.print(f"[yellow]MMS-TTS synthesize error ({lang}): {e}[/yellow]")
            return self._fallback_wav_bytes(text)

    def _fallback_wav_bytes(self, text: str) -> bytes:
        """Emergency WAV bytes fallback using pyttsx3 or silence."""
        import io
        import tempfile
        import os
        import soundfile as sf
        import numpy as np
        try:
            import pyttsx3
            if self._pyttsx3_engine is None:
                self._pyttsx3_engine = pyttsx3.init()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            self._pyttsx3_engine.save_to_file(text, tmp_path)
            self._pyttsx3_engine.runAndWait()
            with open(tmp_path, "rb") as f:
                data = f.read()
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return data
        except Exception:
            buf = io.BytesIO()
            sf.write(buf, np.zeros(1600, dtype=np.float32), samplerate=16000, format="WAV")
            return buf.getvalue()

    def synthesize_to_file(self, text: str, lang: str, output_path: str):
        """Synthesize speech and save to a WAV file."""
        wav_bytes = self.synthesize_to_bytes(text, lang=lang)
        with open(output_path, "wb") as f:
            f.write(wav_bytes)

    def speak(self, text: str, lang: str = "orm"):
        """Speak text aloud using sounddevice or fallback."""
        try:
            import io
            import soundfile as sf
            import sounddevice as sd

            wav_bytes = self.synthesize_to_bytes(text, lang=lang)
            data, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
            sd.play(data, sr)
            sd.wait()
        except Exception as e:
            try:
                import pyttsx3
                if self._pyttsx3_engine is None:
                    self._pyttsx3_engine = pyttsx3.init()
                self._pyttsx3_engine.say(text)
                self._pyttsx3_engine.runAndWait()
            except Exception as e2:
                console.print(f"[yellow]Audio playback error: {e2}[/yellow]")

    def save(self, text: str, output_path: str, lang: str = "orm"):
        """Save speech to file."""
        self.synthesize_to_file(text, lang=lang, output_path=output_path)


# Backward compatibility alias
SimpleTTS = MMSTTSEngine


# ──────────────────────────────────────────────
# Full Pipeline
# ──────────────────────────────────────────────
class TranslatorPipeline:
    """
    End-to-end translation pipeline with lazy model loading.
    
    Memory-efficient design:
      - DatasetEtHoheSTT: official Dataset.ET model for Amharic STT (16.1% WER)
      - EthioMultilingualSTT: handles Oromo + Tigrinya STT (fallback for Amharic)
      - WhisperSTT: handles English + Somali
      - NLLB-200: translation between all 5 languages
      - MMSTTSEngine: Meta MMS-TTS offline neural speech output
    """

    def __init__(self, whisper_size: str = "tiny"):
        self.hohe_stt = DatasetEtHoheSTT()        # Official Dataset.ET Amharic STT
        self.ethio_stt = EthioMultilingualSTT()   # Oromo + Tigrinya STT
        self.stt = WhisperSTT(model_size=whisper_size)  # English + Somali
        self.translator = NLLB200Translator()     # CTranslate2 INT8 (100% offline, ~600MB)
        self.tts = MMSTTSEngine()
        self._loaded = False

    def load_all(self):
        """Load all models. Call once at startup (e.g. app launch)."""
        t0 = time.time()
        console.print(Panel("[bold cyan]Loading Ethiopian Translator (Dataset.ET / Ethio-ASR)[/bold cyan]"))
        try:
            # Prefer the dedicated Amharic model when its local cache is available.
            self.hohe_stt.load()
        except Exception as e:
            console.print(f"[yellow]Amharic ASR note: {e}[/yellow]")
        try:
            # Pre-load EthioMultilingualSTT as universal Ethiopian ASR engine (~2.4GB RAM)
            # Natively covers Amharic, Afaan Oromo, and Tigrinya with zero duplicate model overhead
            self.ethio_stt.load()
        except Exception as e:
            console.print(f"[yellow]ASR pre-load note: {e}[/yellow]")

        self.stt.load()          # English + Somali STT (~200MB RAM)
        self.translator.load()   # NLLB-200 translation (~600MB RAM)
        self.tts.load()          # TTS output
        self._loaded = True
        console.print(Panel(
            f"[bold green]Ready in {time.time()-t0:.0f}s[/bold green]\n"
            f"[dim]5 languages · Dataset.ET & Ethio-ASR official · 100% on-device offline[/dim]"
        ))

    def _transcribe(self, audio_path: str, src_lang_key: str) -> str:
        """Route STT to the correct model for the given language.
        Whisper is strictly forbidden for Amharic, Oromo, and Tigrinya.
        """
        # 1. Ethiopian local languages: EthioMultilingualSTT (Amharic, Afaan Oromo, Tigrinya)
        if src_lang_key in ("amh", "orm", "tir"):
            # Check if Hohe was specifically pre-loaded for Amharic
            if src_lang_key == "amh" and self.hohe_stt.model is not None:
                return self.hohe_stt.transcribe(audio_path)

            if self.ethio_stt.model is None:
                self.ethio_stt.try_load()
            if self.ethio_stt.model is not None:
                lang_code = "am" if src_lang_key == "amh" else ("om" if src_lang_key == "orm" else "ti")
                return self.ethio_stt.transcribe(audio_path, lang_code)
            raise RuntimeError(
                f"EthioMultilingualSTT failed to load for {src_lang_key}. "
                "Whisper fallback is blocked for Horn of Africa languages."
            )

        # 2. English and Somali: Whisper
        whisper_lang = LANGUAGES.get(src_lang_key, {}).get("whisper_code", "en")
        return self.stt.transcribe(audio_path, whisper_lang)

    def _match_social_patterns(self, text: str, src_lang: str, tgt_lang: str) -> str | None:
        """Pattern-match conversational introductions, identity disclosures, and reciprocal inquiries."""
        import re
        t = text.strip()
        t_clean = re.sub(r"[\s.?!።፧!]+$", "", t).strip()

        # Amharic Source Patterns
        if src_lang in ("amh", "amh_Ethi"):
            # 1. Self-introduction: "እኔ [ስም] እባላለሁ" or "[ስም] እባላለሁ" or "ስሜ [ስም] ይባላል"
            m_intro = re.match(r"^(?:እኔ\s+)?([^\s]+)\s+እባላለሁ$", t_clean) or re.match(r"^(?:ስሜ\s+)?([^\s]+)\s+ይባላል$", t_clean)
            if m_intro:
                name = m_intro.group(1).strip()
                name_map = {
                    "ኤርምያስ": {"orm": "Ermiyaas", "eng": "Ermias", "tir": "ኤርምያስ", "som": "Ermiyaas"},
                }
                mapped = name_map.get(name, {})
                t_name = mapped.get(tgt_lang, name)
                if tgt_lang in ("orm", "gaz_Latn"):
                    return f"Ani {t_name} jedhama."
                elif tgt_lang in ("eng", "eng_Latn"):
                    return f"My name is {t_name}."
                elif tgt_lang in ("tir", "tir_Ethi"):
                    return f"ኣነ {t_name} እበሃል ።"
                elif tgt_lang in ("som", "som_Latn"):
                    return f"Waxaa la i yiraahdaa {t_name}."

            # 2. Reciprocal name inquiry: "አንተስ ማን ትባላለህ ወንድሜ?"
            if re.search(r"^(?:አንተስ|አንቺስ)\s+(?:ማን\s+(?:ትባላለህ|ትባያለሽ)|ስምህ\s+ማን\s+ነው|ስምሽ\s+ማን\s+ነው)", t_clean):
                has_brother = bool(re.search(r"(?:ወንድሜ|ወንድም)$", t_clean))
                has_sister = bool(re.search(r"(?:እህቴ|እህት)$", t_clean))
                if tgt_lang in ("orm", "gaz_Latn"):
                    if has_brother:
                        return "Ati hoo maqaan kee eenyu obboleessa koo?"
                    elif has_sister:
                        return "Ati hoo maqaan kee eenyu obboleettii koo?"
                    else:
                        return "Ati hoo maqaan kee eenyu?"
                elif tgt_lang in ("eng", "eng_Latn"):
                    if has_brother:
                        return "And what is your name, my brother?"
                    elif has_sister:
                        return "And what is your name, my sister?"
                    else:
                        return "And what is your name?"
                elif tgt_lang in ("tir", "tir_Ethi"):
                    if has_brother:
                        return "ንስኻኸ መን ትበሃል ሓወይ?"
                    elif has_sister:
                        return "ንስኺኸ መን ትበሃሊ ሓፍተይ?"
                    else:
                        return "ንስኻኸ መን ትበሃል?"
                elif tgt_lang in ("som", "som_Latn"):
                    if has_brother:
                        return "Adigana magacaa walaal?"
                    else:
                        return "Adigana magacaa?"

            # 2b. Conversational greetings and inquiries (ሰላም / እንዴት ነህ / ደህና ነህ / etc.)
            m_greet = re.match(r'^(?:ሰላም\s+)?(?:(ወንድሜ|እህቴ|ወዳጄ|ጓደኛዬ)\s+)?(?:እንዴት|ደህና|ሰላም)\s+(?:ነህ|ነሽ|ናችሁ|ነው|ኖት|ነዎት)(?:\s+(ወንድሜ|እህቴ|ወዳጄ|ጓደኛዬ))?$', t_clean)
            if m_greet:
                title = m_greet.group(1) or m_greet.group(2)
                if tgt_lang in ('eng', 'eng_Latn'):
                    t_map = {'ወንድሜ': 'my brother', 'እህቴ': 'my sister', 'ወዳጄ': 'my friend', 'ጓደኛዬ': 'my friend'}
                    return f'Hello, how are you, {t_map[title]}?' if title else 'Hello, how are you?'
                elif tgt_lang in ('orm', 'gaz_Latn'):
                    t_map = {'ወንድሜ': 'obboleessa koo', 'እህቴ': 'obboleettii koo', 'ወዳጄ': 'hiriyyaa koo', 'ጓደኛዬ': 'hiriyyaa koo'}
                    return f'Akkam jirta {t_map[title]}?' if title else 'Akkam jirta?'
                elif tgt_lang in ('tir', 'tir_Ethi'):
                    t_map = {'ወንድሜ': 'ሓወይ', 'እህቴ': 'ሓፍተይ', 'ወዳጄ': 'መሓዛይ', 'ጓደኛዬ': 'መሓዛይ'}
                    return f'ሰላም ከመይ ኣለኻ {t_map[title]}?' if title else 'ሰላም ከመይ ኣለኻ?'
                elif tgt_lang in ('som', 'som_Latn'):
                    return 'Sidee tahay walaal?' if title else 'Sidee tahay?'

            m_salute = re.match(r'^ሰላም(?:\s+(ወንድሜ|እህቴ|ወዳጄ|ጓደኛዬ))?$', t_clean)
            if m_salute:
                title = m_salute.group(1)
                if tgt_lang in ('eng', 'eng_Latn'):
                    t_map = {'ወንድሜ': 'my brother', 'እህቴ': 'my sister', 'ወዳጄ': 'my friend', 'ጓደኛዬ': 'my friend'}
                    return f'Hello, {t_map[title]}!' if title else 'Hello!'
                elif tgt_lang in ('orm', 'gaz_Latn'):
                    t_map = {'ወንድሜ': 'obboleessa koo', 'እህቴ': 'obboleettii koo', 'ወዳጄ': 'hiriyyaa koo', 'ጓደኛዬ': 'hiriyyaa koo'}
                    return f'Nagaa {t_map[title]}!' if title else 'Akkam!'
                elif tgt_lang in ('tir', 'tir_Ethi'):
                    t_map = {'ወንድሜ': 'ሓወይ', 'እህቴ': 'ሓፍተይ', 'ወዳጄ': 'መሓዛይ', 'ጓደኛዬ': 'መሓዛይ'}
                    return f'ሰላም {t_map[title]}!' if title else 'ሰላም!'
                elif tgt_lang in ('som', 'som_Latn'):
                    return 'Nabad walaal!' if title else 'Nabad!'

            if re.search(r'^ሰላም\s+ጤና\s+ይስጥልኝ$', t_clean):
                if tgt_lang in ('eng', 'eng_Latn'):
                    return 'Hello, greetings!'
                elif tgt_lang in ('orm', 'gaz_Latn'):
                    return "Nagaa fi fayyaan isiniif haa ta'u."
                elif tgt_lang in ('tir', 'tir_Ethi'):
                    return 'ጥዕና ይሃበለይ ።'
                elif tgt_lang in ('som', 'som_Latn'):
                    return 'Nabad iyo caafimaad.'

            if re.search(r'^ሰላም\s+(?:እደር|እደሪ|እደሩ)$', t_clean):
                if tgt_lang in ('eng', 'eng_Latn'):
                    return 'Good night.'
                elif tgt_lang in ('orm', 'gaz_Latn'):
                    return 'Nagaan buli.'
                elif tgt_lang in ('tir', 'tir_Ethi'):
                    return 'ደሓን ሕደር ።'
                elif tgt_lang in ('som', 'som_Latn'):
                    return 'Habeen wanaagsan.'

            if re.search(r'^በሰላም\s+(?:ዋልክ|ዋልሽ|ዋላችሁ|ዋል)$', t_clean):
                if tgt_lang in ('eng', 'eng_Latn'):
                    return 'Good afternoon, have a good day.'
                elif tgt_lang in ('orm', 'gaz_Latn'):
                    return 'Akkam ooltan.'
                elif tgt_lang in ('tir', 'tir_Ethi'):
                    return 'ከመይ ውዒልኩም ።'
                elif tgt_lang in ('som', 'som_Latn'):
                    return 'Galab wanaagsan.'

            # 3. Conversational time-of-day greetings
            if re.search(r"^እንደምን\s+(?:አደሩ|አደርክ|አደርሽ|አደራችሁ)$", t_clean):
                if tgt_lang in ("eng", "eng_Latn"):
                    return "Good morning."
                elif tgt_lang in ("orm", "gaz_Latn"):
                    return "Akkam bultan."
                elif tgt_lang in ("tir", "tir_Ethi"):
                    return "ከመይ ሓዲርኩም ።"
                elif tgt_lang in ("som", "som_Latn"):
                    return "Subax wanaagsan."

            if re.search(r"^እንደምን\s+(?:ዋሉ|ዋልክ|ዋልሽ|ዋላችሁ)$", t_clean):
                if tgt_lang in ("eng", "eng_Latn"):
                    return "Good afternoon."
                elif tgt_lang in ("orm", "gaz_Latn"):
                    return "Akkam ooltan."
                elif tgt_lang in ("tir", "tir_Ethi"):
                    return "ከመይ ውዒልኩም ።"
                elif tgt_lang in ("som", "som_Latn"):
                    return "Galab wanaagsan."

            if re.search(r"^እንደምን\s+(?:አመሹ|አመሸህ|አመሸሽ|አመሻችሁ)$", t_clean):
                if tgt_lang in ("eng", "eng_Latn"):
                    return "Good evening."
                elif tgt_lang in ("orm", "gaz_Latn"):
                    return "Akkam dhiitan."
                elif tgt_lang in ("tir", "tir_Ethi"):
                    return "ከመይ ኣምሲኹም ።"
                elif tgt_lang in ("som", "som_Latn"):
                    return "Fiid wanaagsan."

        # Afaan Oromo Source Patterns
        elif src_lang in ("orm", "gaz_Latn"):
            m_intro = re.match(r"^(?:ani\s+)?([A-Za-z]+)(?:n)?\s+jedhama$", t_clean, re.IGNORECASE) or re.match(r"^maqaan\s+koo\s+([A-Za-z]+)(?:\s+dha)?$", t_clean, re.IGNORECASE)
            if m_intro:
                name = m_intro.group(1).strip()
                if tgt_lang in ("amh", "amh_Ethi"):
                    return f"እኔ {name} እባላለሁ።"
                elif tgt_lang in ("eng", "eng_Latn"):
                    return f"My name is {name}."
                elif tgt_lang in ("tir", "tir_Ethi"):
                    return f"ኣነ {name} እበሃል ።"
                elif tgt_lang in ("som", "som_Latn"):
                    return f"Waxaa la i yiraahdaa {name}."

            if re.search(r"^ati\s+hoo\s+(?:maqaan\s+kee\s+eenyu|eenyu\s+jedhamta)", t_clean, re.IGNORECASE):
                has_brother = bool(re.search(r"obboleessa\s+koo$", t_clean, re.IGNORECASE))
                has_sister = bool(re.search(r"obboleettii\s+koo$", t_clean, re.IGNORECASE))
                if tgt_lang in ("amh", "amh_Ethi"):
                    if has_brother:
                        return "አንተስ ማን ትባላለህ ወንድሜ?"
                    elif has_sister:
                        return "አንቺስ ማን ትባያለሽ እህቴ?"
                    else:
                        return "አንተስ ማን ትባላለህ?"
                elif tgt_lang in ("eng", "eng_Latn"):
                    if has_brother:
                        return "And what is your name, my brother?"
                    else:
                        return "And what is your name?"

            m_orm_greet = re.match(r'^(?:harka fuune|akkam|nagaa dhaa|fayyaa dhaa)(?:\s+(?:jirta|jirtu|bultan|bulte|ooltan|oolte))?(?:\s+(obboleessa koo|obboleettii koo|hiriyyaa koo))?$', t_clean, re.IGNORECASE)
            if m_orm_greet:
                title = (m_orm_greet.group(1) or "").lower()
                has_bro = "obboleessa" in title
                has_sis = "obboleettii" in title
                if tgt_lang in ("eng", "eng_Latn"):
                    if has_bro: return "Hello, how are you, my brother?"
                    if has_sis: return "Hello, how are you, my sister?"
                    return "Hello, how are you?"
                elif tgt_lang in ("amh", "amh_Ethi"):
                    if has_bro: return "እንዴት ነህ ወንድሜ?"
                    if has_sis: return "እንዴት ነሽ እህቴ?"
                    return "እንዴት ነህ?"
                elif tgt_lang in ("tir", "tir_Ethi"):
                    if has_bro: return "ሰላም ከመይ ኣለኻ ሓወይ?"
                    if has_sis: return "ሰላም ከመይ ኣለኺ ሓፍተይ?"
                    return "ሰላም ከመይ ኣለኻ?"
                elif tgt_lang in ("som", "som_Latn"):
                    return "Sidee tahay walaal?" if (has_bro or has_sis) else "Sidee tahay?"

        # Tigrinya Source Patterns
        elif src_lang in ("tir", "tir_Ethi"):
            # 1. Self-introduction: "ኣነ [ስም] እበሃል" or "ስመይ [ስም] ይበሃል"
            m_intro = re.match(r"^(?:ኣነ\s+)?([^\s]+)\s+እበሃል$", t_clean) or re.match(r"^(?:ስመይ\s+)?([^\s]+)\s+ይበሃል$", t_clean)
            if m_intro:
                name = m_intro.group(1).strip()
                if tgt_lang in ("amh", "amh_Ethi"):
                    return f"እኔ {name} እባላለሁ።"
                elif tgt_lang in ("eng", "eng_Latn"):
                    return f"My name is {name}."
                elif tgt_lang in ("orm", "gaz_Latn"):
                    return f"Ani {name} jedhama."
                elif tgt_lang in ("som", "som_Latn"):
                    return f"Waxaa la i yiraahdaa {name}."

            # 2. Reciprocal inquiry: "ንስኻኸ/ንስኺኸ መን ትበሃል?"
            if re.search(r"^(?:ንስኻኸ|ንስኺኸ)\s+መን\s+(?:ትበሃል|ትበሃሊ)", t_clean):
                has_brother = bool(re.search(r"(?:ሓወይ|ሓው)$", t_clean))
                has_sister = bool(re.search(r"(?:ሓፍተይ|ሓብተይ)$", t_clean))
                if tgt_lang in ("amh", "amh_Ethi"):
                    if has_brother:
                        return "አንተስ ማን ትባላለህ ወንድሜ?"
                    elif has_sister:
                        return "አንቺስ ማን ትባያለሽ እህቴ?"
                    else:
                        return "አንተስ ማን ትባላለህ?"
                elif tgt_lang in ("eng", "eng_Latn"):
                    if has_brother:
                        return "And what is your name, my brother?"
                    elif has_sister:
                        return "And what is your name, my sister?"
                    else:
                        return "And what is your name?"
                elif tgt_lang in ("orm", "gaz_Latn"):
                    return "Ati hoo maqaan kee eenyu?"

            m_tir_greet = re.match(r'^(?:ሰላም\s+)?(?:ከመይ\s+(?:ኣለኻ|ኣለኺ|ኣለኹም|ዲኻ|ዲኺ|ዲኹም)|ደሓን\s+(?:ዲኻ|ዲኺ|ዲኹም)|ጥዕና\s+ይሃበለይ)(?:\s+(ሓወይ|ሓፍተይ|መሓዛይ))?$', t_clean)
            if m_tir_greet:
                title = m_tir_greet.group(1) or ""
                has_bro = "ሓወይ" in title
                has_sis = "ሓፍተይ" in title
                if tgt_lang in ("eng", "eng_Latn"):
                    if has_bro: return "Hello, how are you, my brother?"
                    if has_sis: return "Hello, how are you, my sister?"
                    return "Hello, how are you?"
                elif tgt_lang in ("amh", "amh_Ethi"):
                    if has_bro: return "እንዴት ነህ ወንድሜ?"
                    if has_sis: return "እንዴት ነሽ እህቴ?"
                    return "እንዴት ነህ?"
                elif tgt_lang in ("orm", "gaz_Latn"):
                    if has_bro: return "Akkam jirta obboleessa koo?"
                    if has_sis: return "Akkam jirta obboleettii koo?"
                    return "Akkam jirta?"
                elif tgt_lang in ("som", "som_Latn"):
                    return "Sidee tahay walaal?" if (has_bro or has_sis) else "Sidee tahay?"

            # 3. Broadcast anchor introductions:
            # "ጥዕና ይሃበለይ ከመይ ዲኹም ዝኸበርኩም ተመልከትትና/ተዓዘብትና"
            if re.search(r"^(?:ጥዕና\s+ይሃበለይ|ሰላም)\s*(?:፣|,)?\s*(?:ከመይ\s+(?:ዲኹም|ኣለኹም))\s*(?:ዝኸበርኩም|ክቡራት)\s+(?:ተመልከትትና|ተዓዘብትና)", t_clean):
                if tgt_lang in ("eng", "eng_Latn"):
                    return "Hello, how are you honored viewers."
                elif tgt_lang in ("amh", "amh_Ethi"):
                    return "ጤና ይስጥልኝ፣ ክቡራት ተመልካቾቻችን እንደምን ናችሁ።"
                elif tgt_lang in ("orm", "gaz_Latn"):
                    return "Akkam jirtu kabajamoo daawwattoota keenya."
                elif tgt_lang in ("som", "som_Latn"):
                    return "Waxaan idin leenahay caafimaad, sidee tihiin daawadayaasheenna sharafta leh."

            if re.search(r"^(?:ጥዕና\s+ይሃበለይ|ሰላም)\s*(?:፣|,)?\s*(?:ከመይ\s+(?:ዲኹም|ኣለኹም))\s*(?:ዝኸበርኩም|ክቡራት)\s+ሰማዕትና", t_clean):
                if tgt_lang in ("eng", "eng_Latn"):
                    return "Hello, how are you honored listeners."
                elif tgt_lang in ("amh", "amh_Ethi"):
                    return "ጤና ይስጥልኝ፣ ክቡራት አድማጮቻችን እንደምን ናችሁ።"
                elif tgt_lang in ("orm", "gaz_Latn"):
                    return "Akkam jirtu kabajamoo dhaggeeffattoota keenya."
                elif tgt_lang in ("som", "som_Latn"):
                    return "Waxaan idin leenahay caafimaad, sidee tihiin dhagaystayaasheenna sharafta leh."

        # English Source Patterns
        elif src_lang in ("eng", "eng_Latn"):
            m_en_greet = re.match(r"^(?:hello|hi|hey)?\s*(?:how\s+are\s+you|how\s+are\s+you\s+doing|how's\s+it\s+going)(?:,)?\s*(my\s+brother|my\s+sister|my\s+friend|bro)?\??$", t_clean, re.IGNORECASE)
            if m_en_greet:
                title = (m_en_greet.group(1) or "").lower()
                has_bro = "brother" in title or "bro" in title
                has_sis = "sister" in title
                if tgt_lang in ("amh", "amh_Ethi"):
                    if has_bro: return "እንዴት ነህ ወንድሜ?"
                    if has_sis: return "እንዴት ነሽ እህቴ?"
                    return "እንዴት ነህ?"
                elif tgt_lang in ("orm", "gaz_Latn"):
                    if has_bro: return "Akkam jirta obboleessa koo?"
                    if has_sis: return "Akkam jirta obboleettii koo?"
                    return "Akkam jirta?"
                elif tgt_lang in ("tir", "tir_Ethi"):
                    if has_bro: return "ከመይ ኣለኻ ሓወይ?"
                    if has_sis: return "ከመይ ኣለኺ ሓፍተይ?"
                    return "ከመይ ኣለኻ?"
                elif tgt_lang in ("som", "som_Latn"):
                    return "Sidee tahay walaal?" if (has_bro or has_sis) else "Sidee tahay?"

            m_en_salute = re.match(r"^(?:hello|hi|hey)(?:,)?\s*(my\s+brother|my\s+sister|my\s+friend|bro)?[!.]?$", t_clean, re.IGNORECASE)
            if m_en_salute:
                title = (m_en_salute.group(1) or "").lower()
                has_bro = "brother" in title or "bro" in title
                has_sis = "sister" in title
                if tgt_lang in ("amh", "amh_Ethi"):
                    if has_bro: return "ሰላም ወንድሜ!"
                    if has_sis: return "ሰላም እህቴ!"
                    return "ሰላም!"
                elif tgt_lang in ("orm", "gaz_Latn"):
                    if has_bro: return "Nagaa obboleessa koo!"
                    if has_sis: return "Nagaa obboleettii koo!"
                    return "Akkam!"
                elif tgt_lang in ("tir", "tir_Ethi"):
                    if has_bro: return "ሰላም ሓወይ!"
                    if has_sis: return "ሰላም ሓፍተይ!"
                    return "ሰላም!"
                elif tgt_lang in ("som", "som_Latn"):
                    return "Nabad walaal!" if (has_bro or has_sis) else "Nabad!"

        return None

    def _translate_clause(self, clause: str, src_lang_key: str, tgt_lang_key: str) -> tuple[str, bool, list[str]]:
        """Translate a single semantic clause via TM -> Patterns -> Glossary -> EntityShield + NLLB-200.
        Returns: (translated_clause, is_tm_hit, preserved_entities)
        """
        from ai_pipeline.glossary import preprocess_for_translation, postprocess_translation, check_exact_match
        from ai_pipeline.translation_memory import TranslationMemory
        from ai_pipeline.entity_shield import EntityShield

        c_clean = preprocess_for_translation(clause, src_lang_key, tgt_lang_key)
        if not c_clean:
            return "", False, []

        # 1. Direct glossary exact match (curated, hand-verified idiomatic entries take top priority)
        direct_match = check_exact_match(c_clean, src_lang_key, tgt_lang_key)
        if direct_match:
            console.print(f"[cyan]🎯 Direct glossary match: '{c_clean}' -> '{direct_match}'[/cyan]")
            return direct_match, True, []

        # 2. Conversational entity & greeting patterns
        social_match = self._match_social_patterns(c_clean, src_lang_key, tgt_lang_key)
        if social_match:
            console.print(f"[cyan]🎯 Social pattern hit: '{c_clean}' -> '{social_match}'[/cyan]")
            return social_match, True, []

        # 3. High-fidelity conversational Translation Memory (SQLite exact match + strict fuzzy >= 0.95)
        try:
            tm_match = TranslationMemory.get_instance().lookup(c_clean, src_lang_key, tgt_lang_key, min_similarity=0.95)
            if tm_match:
                console.print(f"[cyan]🎯 TM hit ({tm_match.dataset}, score={tm_match.score:.2f}): '{c_clean}' -> '{tm_match.target_text}'[/cyan]")
                return tm_match.target_text, True, []
        except Exception as tm_err:
            console.print(f"[yellow]⚠ TM lookup error: {tm_err}[/yellow]")

        # 4. Entity Shield & Local Offline Neural Machine Translation
        shielded_clause, entities = EntityShield.shield(c_clean, src_lang_key)

        src = LANGUAGES[src_lang_key]["nllb_code"]
        tgt = LANGUAGES[tgt_lang_key]["nllb_code"]
        raw_result = self.translator.translate(shielded_clause, src, tgt)

        if entities:
            raw_result = EntityShield.unshield(raw_result, entities, src_lang_key, tgt_lang_key)

        final_clause = postprocess_translation(raw_result, src_lang_key, tgt_lang_key)
        preserved_names = [e.name_part for e in entities]
        return final_clause, False, preserved_names

    def _translate_base(self, text: str, src_lang_key: str, tgt_lang_key: str) -> dict:
        """Core offline translation: repair -> clause segmentation -> TM / EntityShield / NLLB-200 -> Guard."""
        import re
        from ai_pipeline.speech_repair import SpeechRepair
        from ai_pipeline.glossary import preprocess_for_translation, postprocess_translation
        from ai_pipeline.hallucination_guard import HallucinationGuard

        # 1. On-device speech repair & intent reconstruction
        repaired_text = SpeechRepair.repair(text, src_lang_key)
        clean_text = preprocess_for_translation(repaired_text, src_lang_key, tgt_lang_key)

        if not clean_text:
            return {
                "translated_text": "",
                "confidence": 1.0,
                "is_tm_match": False,
                "entities_preserved": [],
                "warning": None,
            }

        # 2. Full TM check across compound sentences
        try:
            from ai_pipeline.translation_memory import TranslationMemory
            tm_match = TranslationMemory.get_instance().lookup(clean_text, src_lang_key, tgt_lang_key, min_similarity=0.98)
            if tm_match and tm_match.score >= 0.98:
                console.print(f"[cyan]🎯 Full TM exact hit ({tm_match.dataset}): '{clean_text}' -> '{tm_match.target_text}'[/cyan]")
                return {
                    "translated_text": tm_match.target_text,
                    "confidence": 1.0,
                    "is_tm_match": True,
                    "entities_preserved": [],
                    "warning": None,
                }
        except Exception:
            pass

        clauses = [c.strip() for c in re.split(r'(?<=[.?!።፧!])\s+', clean_text) if c.strip()]
        all_tm = True
        preserved_entities: list[str] = []
        translated_clauses: list[str] = []

        UNCLEAR_FALLBACKS = {
            "[Audio unclear]", "[ድምፁ ግልጽ አይደለም]", "[Sagaleen hin dhagahamne]",
            "[ድምጺ ንጹር ኣይኮነን]", "[Codku ma cadda]"
        }

        if len(clauses) > 1:
            for clause in clauses:
                trans, is_tm, ents = self._translate_clause(clause, src_lang_key, tgt_lang_key)
                if not is_tm:
                    all_tm = False
                preserved_entities.extend(ents)
                if trans:
                    trans_str = trans.strip()
                    if tgt_lang_key in ("orm", "eng", "som") and trans_str:
                        trans_str = trans_str[0].upper() + trans_str[1:]
                    if clause.endswith("?") and not trans_str.endswith("?"):
                        trans_str = re.sub(r"[.።]+$", "", trans_str) + "?"
                    elif (clause.endswith("።") or clause.endswith(".")) and not (
                        trans_str.endswith((".", "።", "?", "!")) or trans_str in UNCLEAR_FALLBACKS
                    ):
                        trans_str += "።" if tgt_lang_key in ("amh", "tir") else "."
                    translated_clauses.append(trans_str)

            valid_clauses = [c for c in translated_clauses if c not in UNCLEAR_FALLBACKS]
            assembled = " ".join(valid_clauses) if valid_clauses else (translated_clauses[0] if translated_clauses else "")
        else:
            trans, is_tm, ents = self._translate_clause(clean_text, src_lang_key, tgt_lang_key)
            all_tm = is_tm
            preserved_entities.extend(ents)
            assembled = trans

        # 3. Evaluate output through Hallucination & Degeneration Guard
        guard_res = HallucinationGuard.evaluate(
            source_text=clean_text,
            translated_text=assembled,
            src_lang=src_lang_key,
            tgt_lang=tgt_lang_key,
            is_tm_hit=all_tm,
            entities_shielded=len(preserved_entities),
            entities_restored=len(preserved_entities),
        )

        return {
            "translated_text": guard_res.clean_translation,
            "confidence": guard_res.confidence,
            "is_tm_match": guard_res.is_tm_hit,
            "entities_preserved": preserved_entities,
            "warning": guard_res.warning,
        }

    def translate_text(
        self,
        text: str,
        src_lang_key: str,
        tgt_lang_key: str,
        session_id: str | None = None,
        formality: str = "auto",
    ) -> str:
        """100% Offline translation with contextual reasoning & cultural normalization."""
        smart_res = self.translate_text_smart(
            text, src_lang_key, tgt_lang_key, session_id=session_id, formality=formality
        )
        return smart_res["translated_text"]

    def translate_text_smart(
        self,
        text: str,
        src_lang_key: str,
        tgt_lang_key: str,
        session_id: str | None = None,
        formality: str = "auto",
    ) -> dict:
        """Full contextual translation returning intent, formality, quick-replies, and guard confidence."""
        from ai_pipeline.smart_engine import SmartEngine
        smart_res = SmartEngine.process_and_translate(
            text=text,
            src_lang=src_lang_key,
            tgt_lang=tgt_lang_key,
            session_id=session_id,
            formality=formality,
            nmt_translator_func=self._translate_base,
        )
        return {
            "source_text": smart_res.source_text,
            "translated_text": smart_res.translated_text,
            "src_lang": src_lang_key,
            "tgt_lang": tgt_lang_key,
            "intent": smart_res.intent.value,
            "formality": smart_res.formality,
            "suggested_replies": smart_res.suggested_replies,
            "confidence": smart_res.confidence,
            "is_tm_match": smart_res.is_tm_match,
            "entities_preserved": smart_res.entities_preserved,
            "warning": smart_res.warning,
        }

    def detect_spoken_language(
        self,
        audio_path: str,
        candidate_languages: list[str] | tuple[str, ...] | None = None,
        preferred_target: str = "eng",
        speaker_mode: str = "auto",
    ) -> str:
        """
        Automatic Spoken Language Identification (LID) across:
        - Amharic ('amh')
        - Afaan Oromoo ('orm')
        - Tigrinya ('tir')
        - Somali ('som')
        - English ('eng')
        """
        import re
        import soundfile as sf
        import scipy.signal as sig
        import numpy as np
        import torch

        # Define candidate scope based on speaker_mode
        if speaker_mode == "ethiopian_only":
            candidates = {"amh", "orm", "tir", "som"}
        elif candidate_languages:
            candidates = set(candidate_languages)
        else:
            candidates = {"amh", "orm", "tir", "som", "eng"}

        candidate_order = [language for language in ("amh", "orm", "tir", "som", "eng") if language in candidates]
        if not candidate_order:
            raise ValueError("candidate_languages must contain at least one supported language")

        def fallback_language() -> str:
            """Choose only from the requested candidates when LID is uncertain."""
            whisper_scores = {
                "eng": en_prob,
                "som": so_prob,
                "amh": am_prob,
                "orm": or_prob,
                "tir": ti_prob,
            }
            best_language = max(
                candidate_order,
                key=lambda language: whisper_scores.get(language, 0.0),
            )
            if whisper_scores.get(best_language, 0.0) > 0.0:
                return best_language
            return candidate_order[0]

        # 1. Acoustic Language Check with Whisper (always run for best probs)
        whisper_probs = {}
        if self.stt.model is not None:
            try:
                import whisper
                audio, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                if sample_rate != 16000:
                    num_samples = int(len(audio) * 16000 / sample_rate)
                    audio = sig.resample(audio, num_samples).astype(np.float32)
                audio = WhisperSTT._trim_silence(audio, 16000)
                audio = whisper.pad_or_trim(audio)
                mel = whisper.log_mel_spectrogram(audio)
                _, whisper_probs = self.stt.model.detect_language(mel)
            except Exception as e:
                console.print(f"[yellow]Whisper LID warning: {e}[/yellow]")

        en_prob = whisper_probs.get("en", 0.0)
        so_prob = whisper_probs.get("so", 0.0)
        am_prob = whisper_probs.get("am", 0.0)
        or_prob = whisper_probs.get("om", whisper_probs.get("or", 0.0))
        ti_prob = whisper_probs.get("ti", 0.0)

        # English Speaker Mode: Whisper decisive for English
        if speaker_mode == "english_speaker" and "eng" in candidates:
            if en_prob >= 0.28:
                console.print(f"[green]English detected en={en_prob:.2f} (English Speaker Mode)[/green]")
                return "eng"

        # Auto Mode: High-confidence English wins over Ethio-ASR
        if "eng" in candidates and en_prob >= 0.35 and en_prob > am_prob and en_prob > so_prob:
            console.print(f"[green]High-confidence English (en={en_prob:.2f})[/green]")
            return "eng"

        # 2. Ethiopian Multilingual Model CTC Forward Pass
        raw_decoded = ""
        ctc_scores: dict[str, float] = {}
        ctc_texts: dict[str, str] = {}
        if self.ethio_stt.model is None:
            self.ethio_stt.try_load()

        if self.ethio_stt.model is not None and self.ethio_stt.processor is not None:
            try:
                audio_data, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
                if audio_data.ndim > 1:
                    audio_data = audio_data.mean(axis=1)
                if sample_rate != 16000:
                    num_samples = int(len(audio_data) * 16000 / sample_rate)
                    audio_data = sig.resample(audio_data, num_samples).astype(np.float32)

                audio_data = WhisperSTT._trim_silence(audio_data, 16000)
                if audio_data.size > 0:
                    inputs = self.ethio_stt.processor(
                        audio_data, sampling_rate=16000, return_tensors="pt", padding=True
                    )
                    with torch.no_grad():
                        logits = self.ethio_stt.model(**inputs).logits
                    if hasattr(self.ethio_stt, "score_language_logits"):
                        ctc_scores, ctc_texts = self.ethio_stt.score_language_logits(
                            logits[0].float().cpu().numpy()
                        )
                    if ctc_texts:
                        raw_decoded = max(
                            ctc_texts,
                            key=lambda language_code: ctc_scores[language_code],
                        )
                        raw_decoded = ctc_texts[raw_decoded]
                    else:
                        predicted_ids = torch.argmax(logits, dim=-1)
                        raw_decoded = self.ethio_stt.processor.batch_decode(predicted_ids)[0].strip()
            except Exception as e:
                console.print(f"[yellow]EthioMultilingualSTT LID warning: {e}[/yellow]")

        console.print(f"[cyan]LID Scan -> CTC: '{raw_decoded}' | en={en_prob:.2f}, so={so_prob:.2f}, am={am_prob:.2f}, or={or_prob:.2f}, ti={ti_prob:.2f} [mode={speaker_mode}][/cyan]")

        # Count character types in raw CTC output
        geez_chars = len(re.findall(r"[\u1200-\u137F]", raw_decoded))
        latin_chars = len(re.findall(r"[a-zA-Z]", raw_decoded))
        norm_text = raw_decoded.lower()

        # The multilingual model can emit an explicit language token. Trust it
        # before applying script heuristics, which are only useful as weak evidence.
        token_match = re.search(r"\[(AMH|ORM|TIR|SID|WAL)\]", raw_decoded)
        if token_match and not ctc_scores:
            tok = token_match.group(1)
            if tok == "AMH" and "amh" in candidates: return "amh"
            if tok == "ORM" and "orm" in candidates: return "orm"
            if tok == "TIR" and "tir" in candidates:
                # The model occasionally emits [TIR] for Amharic greetings.
                # Require the decoded text not to contain strong Amharic markers.
                amharic_markers = {"ሰላም", "እንዴት", "ነው", "ነኝ", "ይቅርታ", "ደህና"}
                if not any(marker in raw_decoded for marker in amharic_markers):
                    return "tir"
                if "amh" in candidates:
                    return "amh"

        # Primary Ethiopian LID path: compare language-model scores from the
        # multilingual CTC decoders instead of trusting raw argmax text.
        ctc_language_codes = {
            "amh": "am",
            "orm": "om",
            "tir": "ti",
        }
        scored_candidates = {
            language: ctc_scores[ctc_language_codes[language]]
            for language in candidate_order
            if language in ctc_language_codes and ctc_language_codes[language] in ctc_scores
        }
        if scored_candidates:
            best_language = max(scored_candidates, key=scored_candidates.get)
            if best_language in candidates:
                return best_language

        # -----------------------------------------------------------------
        # ETHIOPIC SCRIPT GUARD: If CTC output is dominantly Ge'ez,
        # skip directly to the Amharic/Tigrinya split.  This prevents
        # a few stray Latin chars from pulling us into the wrong branch.
        # -----------------------------------------------------------------
        if geez_chars >= 3 and geez_chars > latin_chars * 2:
            if candidates == {"amh"}:
                return "amh"
            if candidates == {"tir"}:
                return "tir"

            tir_kw_g = {"ከመይ", "ኣለዛ", "ኣለኺ", "ኣለኹም", "ከካሉክሉይለይየ", "ዲዛ", "ዲኺ", "ዲኹም", "ናይ", "ኣብ", "ዕንታይ", "መን", "ዕወ", "ኣይኮነን", "ይጥሄታ", "ግቡን", "ንሕና"}
            amh_kw_g = {"ዕንዳት", "አለህ", "አለት", "አሉችሁ", "አመሰግናለሁ", "ነኝ", "ነወ", "ነት", "ነህ", "ናችወ", "ምንድን", "ማን", "አወ", "ዕሲ", "አይደለም", "ይቅርታ", "ደህና", "ሰላም"}
            tir_m = sum(1 for kw in tir_kw_g if kw in raw_decoded)
            amh_m = sum(1 for kw in amh_kw_g if kw in raw_decoded)

            if tir_m > amh_m and "tir" in candidates:
                return "tir"
            return "amh" if "amh" in candidates else fallback_language()

        # English keyword check — require 3+ UNIQUE hits with zero Ge'ez chars.
        # This prevents CTC noise from Ethiopian speech spuriously matching English words.
        eng_keywords = {
            "hello", "hi", "how", "are", "you", "what", "where", "when", "why", "who",
            "good", "morning", "afternoon", "evening", "thank", "thanks", "please",
            "name", "is", "the", "this", "that", "can", "help", "need", "want",
            "doctor", "hospital", "yes", "no", "okay", "sorry", "speak", "english", "understand",
        }
        eng_hits = len({w for w in re.findall(r"\b[a-z]+\b", norm_text) if w in eng_keywords})
        if "eng" in candidates and geez_chars == 0 and (en_prob >= 0.30 or eng_hits >= 3):
            return "eng"

        # -----------------------------------------------------------------
        # Branch 1: Ethiopic Script Present (Amharic vs Tigrinya)
        # -----------------------------------------------------------------
        if geez_chars > 0 and geez_chars >= latin_chars:
            if candidates == {"amh"}:
                return "amh"
            if candidates == {"tir"}:
                return "tir"

            tir_keywords = {"ከመይ", "ኣለዛ", "ኣለኺ", "ኣለኹም", "ከካሉክሉይለይየ", "ዲዛ", "ዲኺ", "ዲኹም", "ናይ", "ኣብ", "ዕንታይ", "መን", "ዕወ", "ኣይኮነን", "ይጥሄታ", "ግቡን", "ንሕና"}
            amh_keywords = {"ዕንዳት", "አለህ", "አለት", "አሉችሁ", "አመሰግናለሁ", "ነኝ", "ነወ", "ነት", "ነህ", "ናችወ", "ምንድን", "ማን", "አወ", "ዕሲ", "አይደለም", "ይቅርታ", "ደህና", "ሰላም"}

            tir_matches = sum(1 for kw in tir_keywords if kw in raw_decoded)
            amh_matches = sum(1 for kw in amh_keywords if kw in raw_decoded)

            if tir_matches > amh_matches and "tir" in candidates:
                return "tir"
            return "amh" if "amh" in candidates else fallback_language()

        # -----------------------------------------------------------------
        # Branch 2: Latin Script Dominated (Oromo, Somali, English)
        # -----------------------------------------------------------------
        # Somali: require 2+ keyword hits OR Whisper >= 0.35
        som_keywords = {
            "sidee", "tahay", "tihiin", "mahadsanid", "waa", "adiga", "aniga", "maxaa",
            "xagee", "magacaa", "subax", "galab", "wanaagsan", "fiican", "fadlan",
            "haa", "maya", "nabad", "barasho",
        }
        som_hits = sum(1 for w in re.findall(r"\b[a-z]+\b", norm_text) if w in som_keywords)
        if "som" in candidates and (so_prob >= 0.35 or som_hits >= 2):
            return "som"

        # Oromo: require 1+ keyword hit.
        # Qubee doubled vowels (aa/ee/oo) alone are NOT sufficient because English has
        # them too ("food", "need", "tool") -- they only count alongside a keyword.
        orm_keywords = {
            "akkam", "jirtu", "jirta", "fayyaa", "baga", "nagaan", "dhuftan", "galatoomi",
            "maal", "eessa", "eenyu", "ani", "ati", "maqaan", "koo", "jedhama", "waan",
            "gaarii", "isbitaala", "obboo", "aaddee", "nagaa", "hundaa", "tokkoo", "lamaan",
        }
        orm_hits = sum(1 for w in re.findall(r"\b[a-z']+\b", norm_text) if w in orm_keywords)
        has_qubee_doubles = bool(re.search(r"(?:aa|ee|oo|uu|ii)", norm_text)) and orm_hits >= 1
        if "orm" in candidates and (orm_hits >= 1 or has_qubee_doubles):
            return "orm"

        # Final fallback using Whisper residual probabilities
        if "eng" in candidates and en_prob > 0.22:
            return "eng"
        if "orm" in candidates:
            return "orm"
        if "som" in candidates:
            return "som"
        if "amh" in candidates and am_prob > 0.25:
            return "amh"

        return fallback_language()

    def _detect_audio_language(self, audio_path: str, pair: tuple[str, str]) -> str | None:
        """Fast ~15ms acoustic language check between the conversation languages."""
        try:
            return self.detect_spoken_language(audio_path, candidate_languages=list(pair))
        except Exception:
            return None
    @staticmethod
    def _split_audio_segments(
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        min_silence_duration: float = 0.35,
        silence_threshold: float = 0.03,
    ) -> list[np.ndarray]:
        """
        Segment speech by natural acoustic pauses (>350ms of relative silence).
        Prevents ASR and NMT sequence length drift and attention hallucination
        without requiring hardcoded sentence boundary regexes.
        """
        if len(audio_data) < sample_rate * 3.0:
            return [audio_data]

        peak = float(np.max(np.abs(audio_data)))
        # Any signal below 0.025 peak is background room noise/silence
        if peak < 0.025:
            return []

        thresh = max(0.015, peak * silence_threshold)
        window_size = max(1, int(sample_rate * 0.02))  # 20ms
        energy = np.convolve(np.abs(audio_data), np.ones(window_size, dtype=np.float32) / window_size, mode="same")
        is_speech = energy >= thresh

        min_silence_samples = int(sample_rate * min_silence_duration)
        min_speech_samples = int(sample_rate * 0.5)

        segments = []
        seg_start = None
        silence_count = 0

        for i, speech in enumerate(is_speech):
            if speech:
                if seg_start is None:
                    seg_start = max(0, i - int(sample_rate * 0.05))
                silence_count = 0
            else:
                if seg_start is not None:
                    silence_count += 1
                    if silence_count >= min_silence_samples:
                        seg_end = min(len(audio_data), i - silence_count + int(sample_rate * 0.05))
                        if (seg_end - seg_start) >= min_speech_samples:
                            segments.append(audio_data[seg_start:seg_end])
                        seg_start = None
                        silence_count = 0

        if seg_start is not None:
            seg_end = len(audio_data)
            if (seg_end - seg_start) >= min_speech_samples:
                segments.append(audio_data[seg_start:seg_end])

        # If too many tiny segments detected, audio is likely fluctuating noise rather than clean speech
        if len(segments) > 6:
            return [audio_data]

        return segments if segments else [audio_data]

    def _transcribe_robust(self, audio_path: str, src_lang_key: str) -> str:
        """Transcribe audio file with automatic acoustic pause chunking for scalable multi-sentence speech."""
        import soundfile as sf
        import scipy.signal as sig
        import tempfile

        audio_data, sample_rate = sf.read(audio_path, dtype="float32", always_2d=False)
        if audio_data.ndim > 1:
            audio_data = audio_data.mean(axis=1)
        if sample_rate != 16000:
            num_samples = int(len(audio_data) * 16000 / sample_rate)
            audio_data = sig.resample(audio_data, num_samples).astype(np.float32)
            sample_rate = 16000

        # Overall audio energy check: discard pure ambient silence
        peak = float(np.max(np.abs(audio_data)))
        if peak < 0.02:
            return ""

        segments = self._split_audio_segments(audio_data, sample_rate)
        if len(segments) <= 1:
            return self._transcribe(audio_path, src_lang_key)

        console.print(f"[cyan]🎙 Acoustic silence segmentation: identified {len(segments)} natural speech clauses[/cyan]")
        transcribed_parts = []
        term = "።" if src_lang_key in ("amh", "tir") else "."
        for seg in segments:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                sf.write(tmp_path, seg, sample_rate)
                part = self._transcribe(tmp_path, src_lang_key).strip()
                if part:
                    if not part.endswith((".", "።", "?", "!")):
                        part += term
                    transcribed_parts.append(part)
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        return " ".join(transcribed_parts) if transcribed_parts else self._transcribe(audio_path, src_lang_key)

    def translate_audio(
        self,
        audio_path: str,
        src_lang_key: str,
        tgt_lang_key: str,
        speak_result: bool = True,
        session_id: str | None = None,
        formality: str = "auto",
        speaker_mode: str = "auto",
    ) -> dict:
        """Full pipeline: audio file → transcribe → smart translate → (optionally speak)."""
        effective_src = src_lang_key
        effective_tgt = tgt_lang_key

        # Step 0: Spoken Language Identification & Auto-Routing
        if src_lang_key in ("auto", "detect", None) or src_lang_key not in LANGUAGES:
            detected = self.detect_spoken_language(
                audio_path,
                preferred_target=tgt_lang_key,
                speaker_mode=speaker_mode,
            )
            effective_src = detected
            console.print(f"[yellow]⚡ Spoken language automatically identified: '{LANGUAGES[detected]['name']}' ({detected}) [mode={speaker_mode}][/yellow]")
            if speaker_mode == "english_speaker":
                if effective_src == "eng":
                    effective_tgt = tgt_lang_key if tgt_lang_key != "eng" else "amh"
                else:
                    if tgt_lang_key and tgt_lang_key not in ("auto", "detect", effective_src):
                        effective_tgt = tgt_lang_key
                    else:
                        effective_tgt = "eng"
            elif speaker_mode == "ethiopian_only":
                if effective_src == effective_tgt:
                    effective_tgt = "amh" if effective_src != "amh" else "orm"
            else:
                if effective_src == effective_tgt:
                    effective_tgt = "eng" if effective_src != "eng" else "amh"
        else:
            detected = self._detect_audio_language(audio_path, (src_lang_key, tgt_lang_key))
            if detected and detected != src_lang_key and detected in (src_lang_key, tgt_lang_key):
                console.print(f"[yellow]⚡ Auto-routed speech: detected '{detected}' (swapped from '{src_lang_key}')[/yellow]")
                effective_src = detected
                effective_tgt = src_lang_key if detected == tgt_lang_key else tgt_lang_key

        src_lang = LANGUAGES[effective_src]
        tgt_lang = LANGUAGES[effective_tgt]

        console.print(f"\n[bold]Pipeline: {src_lang['name']} → {tgt_lang['name']}[/bold]")

        # Step 1: STT (routes to best model per language with acoustic pause chunking)
        t0 = time.time()
        console.print("[cyan]Step 1: Transcribing speech (Dataset.ET / ASR)...[/cyan]")
        raw_transcribed = self._transcribe_robust(audio_path, effective_src)
        from ai_pipeline.speech_repair import SpeechRepair
        transcribed = SpeechRepair.repair(raw_transcribed, effective_src)
        stt_time = time.time() - t0
        console.print(f"[green]  Transcribed ({stt_time:.1f}s): '{transcribed}'[/green]")

        if not transcribed or not transcribed.strip():
            console.print("[yellow]⚠ No clear speech detected in audio.[/yellow]")
            return {
                "source_text": "",
                "translated_text": "",
                "src_lang": effective_src,
                "tgt_lang": effective_tgt,
                "intent": "general_conversation",
                "formality": formality,
                "suggested_replies": [],
                "confidence": 0.0,
                "is_tm_match": False,
                "entities_preserved": [],
                "warning": "No speech detected. Please speak closer to the microphone.",
                "stt_time": round(stt_time, 2),
                "trans_time": 0.0,
                "tts_time": 0.0,
                "total_time": round(stt_time, 2),
            }

        # Step 2: Smart Translation (with context, intent, and suggestions)
        t1 = time.time()
        console.print("[cyan]Step 2: Smart Translating...[/cyan]")
        smart_res = self.translate_text_smart(
            transcribed, effective_src, effective_tgt, session_id=session_id, formality=formality
        )
        translated = smart_res["translated_text"]
        trans_time = time.time() - t1
        console.print(f"[green]  Translated ({trans_time:.1f}s) [{smart_res['intent']}]: '{translated}'[/green]")

        # Step 3: TTS (speak for the other person to hear)
        tts_time = 0.0
        if speak_result:
            t2 = time.time()
            console.print("[cyan]Step 3: Speaking translation...[/cyan]")
            self.tts.speak(translated, lang=effective_tgt)
            tts_time = time.time() - t2
            console.print(f"[green]  Spoken ({tts_time:.1f}s)[/green]")

        total_time = time.time() - t0
        console.print(f"\n[bold green]Total latency: {total_time:.1f}s[/bold green]")

        return {
            "source_text": smart_res["source_text"],
            "translated_text": smart_res["translated_text"],
            "src_lang": effective_src,
            "tgt_lang": effective_tgt,
            "intent": smart_res["intent"],
            "formality": smart_res["formality"],
            "suggested_replies": smart_res["suggested_replies"],
            "confidence": smart_res.get("confidence", 0.90),
            "is_tm_match": smart_res.get("is_tm_match", False),
            "entities_preserved": smart_res.get("entities_preserved", []),
            "warning": smart_res.get("warning", None),
            "stt_time": round(stt_time, 2),
            "trans_time": round(trans_time, 2),
            "tts_time": round(tts_time, 2),
            "total_time": round(total_time, 2),
        }

    def live_translate(self, src_lang_key: str, tgt_lang_key: str, duration: int = 5):
        """Record from mic and translate in real-time."""
        audio_path = self.stt.record_audio(duration=duration)
        result = self.translate_audio(audio_path, src_lang_key, tgt_lang_key)
        os.unlink(audio_path)
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
            pipeline.tts.speak(result, lang=tgt)

        elif choice == "2":
            secs = input("Recording duration in seconds (default 5): ").strip()
            duration = int(secs) if secs.isdigit() else 5
            result = pipeline.live_translate(src, tgt, duration=duration)
            console.print(f"\n[bold]Result:[/bold]")
            console.print(f"  Source    : {result['source_text']}")
            console.print(f"  Translated: [bold green]{result['translated_text']}[/bold green]")


if __name__ == "__main__":
    run_demo()
