"""Mikrofon-Aufnahme mit einfacher Sprachaktivitaets-Erkennung (VAD).

Segmentiert einen kontinuierlichen Mikrofon-Stream in einzelne
Sprach-Abschnitte (Utterances), die dann an Whisper zur Erkennung
uebergeben werden koennen. Whisper selbst kann keine echten
Wort-fuer-Wort-Streams verarbeiten, daher ist dieser Chunk-Ansatz
("Aufnehmen bis Stille, dann erkennen") das uebliche Verfahren fuer
Whisper-basierte Nahezu-Echtzeit-Anwendungen.
"""
from __future__ import annotations

import collections
import queue
import sys
import threading
from dataclasses import dataclass

import numpy as np
import sounddevice as sd
import webrtcvad

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000
FRAME_BYTES = FRAME_SAMPLES * 2  # int16 mono


@dataclass
class UtteranceConfig:
    vad_aggressiveness: int = 2
    silence_ms_to_stop: int = 700
    min_speech_ms: int = 300
    max_utterance_s: float = 20.0


class MicrophoneUtteranceStream:
    """Liest vom Standard-Mikrofon und liefert fertige Sprach-Segmente.

    Nutzung:
        stream = MicrophoneUtteranceStream()
        stream.start()
        for audio_f32 in stream.utterances():
            ...  # an Whisper uebergeben
        stream.stop()
    """

    def __init__(self, config: UtteranceConfig | None = None, device: int | str | None = None):
        self.config = config or UtteranceConfig()
        self.device = device
        self._vad = webrtcvad.Vad(self.config.vad_aggressiveness)
        self._frame_queue: "queue.Queue[bytes]" = queue.Queue()
        self._stream: sd.RawInputStream | None = None
        self._stop_event = threading.Event()

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[Audio] Status: {status}", file=sys.stderr)
        self._frame_queue.put(bytes(indata))

    def start(self):
        self._stop_event.clear()
        self._stream = sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=FRAME_SAMPLES,
            device=self.device,
            dtype="int16",
            channels=1,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        self._stop_event.set()
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._frame_queue.mutex:
            self._frame_queue.queue.clear()

    def utterances(self):
        """Generator: liefert fertige Sprachsegmente als float32-numpy-Array (16kHz mono)."""
        silence_frames_to_stop = self.config.silence_ms_to_stop // FRAME_MS
        min_speech_frames = self.config.min_speech_ms // FRAME_MS
        max_frames = int(self.config.max_utterance_s * 1000 // FRAME_MS)

        triggered = False
        voiced_frames: list[bytes] = []
        ring_buffer: collections.deque = collections.deque(maxlen=silence_frames_to_stop)

        while not self._stop_event.is_set():
            try:
                frame = self._frame_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if len(frame) != FRAME_BYTES:
                continue

            is_speech = self._vad.is_speech(frame, SAMPLE_RATE)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, s in ring_buffer if s])
                if num_voiced > 0.5 * ring_buffer.maxlen:
                    triggered = True
                    voiced_frames.extend(f for f, _ in ring_buffer)
                    ring_buffer.clear()
            else:
                voiced_frames.append(frame)
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, s in ring_buffer if not s])
                too_long = len(voiced_frames) >= max_frames
                if (ring_buffer.maxlen and num_unvoiced >= ring_buffer.maxlen) or too_long:
                    triggered = False
                    if len(voiced_frames) >= min_speech_frames:
                        yield self._to_float32(voiced_frames)
                    voiced_frames = []
                    ring_buffer.clear()

    @staticmethod
    def _to_float32(frames: list[bytes]) -> np.ndarray:
        raw = b"".join(frames)
        audio_i16 = np.frombuffer(raw, dtype=np.int16)
        return audio_i16.astype(np.float32) / 32768.0


def list_input_devices():
    """Hilfsfunktion zum Auflisten verfuegbarer Mikrofone (fuer die Konfiguration)."""
    devices = sd.query_devices()
    return [
        (idx, d["name"])
        for idx, d in enumerate(devices)
        if d.get("max_input_channels", 0) > 0
    ]
