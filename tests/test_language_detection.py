import types
import unittest
from unittest.mock import patch

import numpy as np

from ai_pipeline.pipeline import TranslatorPipeline


class FakeLogits:
    def __getitem__(self, _index):
        return self

    def float(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return np.zeros((1, 1), dtype=np.float32)


class LanguageDetectionTests(unittest.TestCase):
    def make_pipeline(self, whisper_probs: dict[str, float], decoded: str = "") -> TranslatorPipeline:
        pipeline = TranslatorPipeline.__new__(TranslatorPipeline)
        pipeline.stt = types.SimpleNamespace(
            model=types.SimpleNamespace(
                detect_language=lambda _mel: (None, whisper_probs),
            )
        )
        pipeline.ethio_stt = types.SimpleNamespace(model=None, processor=None, try_load=lambda: None)
        if decoded:
            pipeline.ethio_stt.model = lambda **_inputs: types.SimpleNamespace(logits=FakeLogits())
            pipeline.ethio_stt.processor = lambda *_args, **_inputs: {}
            pipeline.ethio_stt.processor.batch_decode = lambda _ids: [decoded]
        whisper = types.SimpleNamespace(
            load_audio=lambda _path: np.zeros(16000, dtype=np.float32),
            pad_or_trim=lambda audio: audio,
            log_mel_spectrogram=lambda audio: audio,
        )
        pipeline._whisper_module = whisper
        pipeline._decoded_for_test = decoded
        return pipeline

    def dependency_modules(self, pipeline: TranslatorPipeline) -> dict[str, types.ModuleType]:
        signal = types.ModuleType("scipy.signal")
        signal.resample = lambda audio, _size: audio
        scipy = types.ModuleType("scipy")
        scipy.signal = signal
        torch = types.ModuleType("torch")
        if pipeline._decoded_for_test:
            class NoGrad:
                def __enter__(self):
                    return self

                def __exit__(self, *_args):
                    return False

            torch.no_grad = lambda: NoGrad()
            torch.argmax = lambda _logits, dim: None
        return {
            "whisper": pipeline._whisper_module,
            "scipy": scipy,
            "scipy.signal": signal,
            "torch": torch,
        }

    @patch("soundfile.read", return_value=(np.ones(16000, dtype=np.float32), 16000))
    def test_uncertain_detection_does_not_return_preferred_target(self, _read) -> None:
        pipeline = self.make_pipeline({})
        with patch.dict("sys.modules", self.dependency_modules(pipeline)):
            detected = pipeline.detect_spoken_language(
                "missing.wav",
                candidate_languages=("tir", "eng"),
                preferred_target="eng",
            )

        self.assertEqual(detected, "tir")

    @patch("soundfile.read", return_value=(np.ones(16000, dtype=np.float32), 16000))
    def test_fallback_uses_whisper_probability_within_candidates(self, _read) -> None:
        pipeline = self.make_pipeline({"en": 0.8, "am": 0.1})
        with patch.dict("sys.modules", self.dependency_modules(pipeline)):
            detected = pipeline.detect_spoken_language(
                "missing.wav",
                candidate_languages=("amh", "eng"),
                preferred_target="amh",
            )

        self.assertEqual(detected, "eng")

    @patch("soundfile.read", return_value=(np.ones(16000, dtype=np.float32), 16000))
    def test_ethiopic_keywords_distinguish_amharic_and_tigrinya(self, _read) -> None:
        cases = (("ሰላም እንዴት ነው", "amh"), ("ከመይ ኣለኻ", "tir"))
        for decoded, expected in cases:
            pipeline = self.make_pipeline({}, decoded)
            with patch.dict("sys.modules", self.dependency_modules(pipeline)):
                detected = pipeline.detect_spoken_language(
                    "missing.wav",
                    candidate_languages=("amh", "tir"),
                )
            self.assertEqual(detected, expected, decoded)

    @patch("soundfile.read", return_value=(np.ones(16000, dtype=np.float32), 16000))
    def test_noisy_tigrinya_probability_does_not_override_amharic_text(self, _read) -> None:
        pipeline = self.make_pipeline({"ti": 0.8, "am": 0.1}, "ሰላም እንዴት ነው")
        with patch.dict("sys.modules", self.dependency_modules(pipeline)):
            detected = pipeline.detect_spoken_language(
                "missing.wav",
                candidate_languages=("amh", "tir"),
            )

        self.assertEqual(detected, "amh")

    @patch("soundfile.read", return_value=(np.ones(16000, dtype=np.float32), 16000))
    def test_tigrinya_token_is_overruled_by_amharic_greeting(self, _read) -> None:
        pipeline = self.make_pipeline({}, "[TIR] ሰላም እንዴነ?")
        with patch.dict("sys.modules", self.dependency_modules(pipeline)):
            detected = pipeline.detect_spoken_language(
                "missing.wav",
                candidate_languages=("amh", "tir"),
            )

        self.assertEqual(detected, "amh")

    @patch("soundfile.read", return_value=(np.ones(16000, dtype=np.float32), 16000))
    def test_ctc_language_score_is_primary_over_transcription_token(self, _read) -> None:
        pipeline = self.make_pipeline({}, "[TIR] ሰላም እንዴነ?")
        pipeline.ethio_stt.score_language_logits = lambda _logits: (
            {"am": -1.0, "ti": -4.0},
            {"am": "ሰላም እንዴነ?", "ti": "ሰሎም"},
        )
        with patch.dict("sys.modules", self.dependency_modules(pipeline)):
            detected = pipeline.detect_spoken_language(
                "missing.wav",
                candidate_languages=("amh", "tir"),
            )

        self.assertEqual(detected, "amh")


if __name__ == "__main__":
    unittest.main()