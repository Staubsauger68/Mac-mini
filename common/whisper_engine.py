"""Duenne Wrapper-Schicht um faster-whisper fuer beide Projekte."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from faster_whisper import WhisperModel


@dataclass
class RecognitionResult:
    text: str
    language: str
    language_probability: float


class WhisperEngine:
    def __init__(self, model_size: str = "small", device: str = "auto", compute_type: str = "auto"):
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, audio: np.ndarray, language: str | None = None) -> RecognitionResult:
        """Transkribiert ein Audio-Segment (float32, 16kHz, mono).

        language=None -> automatische Spracherkennung (fuer Projekt A).
        language="de" -> feste Sprache, schneller (fuer Projekt B).
        """
        segments, info = self._model.transcribe(
            audio,
            language=language,
            vad_filter=False,  # VAD passiert bereits vorher beim Aufnehmen
            beam_size=5,
        )
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return RecognitionResult(
            text=text,
            language=info.language,
            language_probability=info.language_probability,
        )
