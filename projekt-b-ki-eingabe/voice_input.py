#!/usr/bin/env python3
"""Projekt B: Deutsche Spracheingabe fuer eine entfernte KI.

Nimmt deutsche Sprache ueber das Mikrofon des Mac mini auf, wandelt sie
per Whisper in Text um und schickt den Text als Prompt an eine KI, die
auf einem anderen Rechner im Netzwerk laeuft (z.B. Ollama/LM Studio auf
einem Mac Studio oder Windows-PC). Die Antwort der KI wird auf diesem
Mac mini angezeigt.
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.audio_stream import MicrophoneUtteranceStream, UtteranceConfig, list_input_devices  # noqa: E402
from common.whisper_engine import WhisperEngine  # noqa: E402

from remote_ai_client import RemoteAIClient  # noqa: E402

load_dotenv(Path(__file__).resolve().parent / ".env")


class VoiceInputApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Whisper -> Entfernte KI")
        self.root.geometry("1000x700")

        self._ui_queue: "queue.Queue[tuple]" = queue.Queue()
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._mic_stream: MicrophoneUtteranceStream | None = None

        self._build_ui()

        url = os.environ.get("REMOTE_AI_URL", "").strip()
        model = os.environ.get("REMOTE_AI_MODEL", "").strip()
        api_key = os.environ.get("REMOTE_AI_API_KEY", "").strip()
        style = os.environ.get("REMOTE_AI_STYLE", "openai").strip()
        if not url or not model:
            messagebox.showerror(
                "Konfiguration fehlt",
                "Bitte REMOTE_AI_URL und REMOTE_AI_MODEL in "
                "projekt-b-ki-eingabe/.env eintragen.",
            )
        self._client = RemoteAIClient(url=url, model=model, api_key=api_key, style=style)

        model_size = os.environ.get("WHISPER_MODEL_SIZE", "small")
        self._status(f"Lade Whisper-Modell '{model_size}' ...")
        self._engine = WhisperEngine(model_size=model_size)
        self._status(f"Bereit. Ziel-KI: {url} ({model})")

        self.root.after(100, self._drain_ui_queue)

    # ---------------------------------------------------------------- UI
    def _build_ui(self):
        self.root.configure(bg="white")

        top = tk.Frame(self.root, bg="white")
        top.pack(fill=tk.X, padx=10, pady=8)

        self.toggle_btn = tk.Button(
            top, text="Talk starten", font=("Helvetica", 16, "bold"),
            command=self._toggle_talk, bg="#2e7d32", fg="white", padx=16, pady=8,
        )
        self.toggle_btn.pack(side=tk.LEFT)

        self.status_label = tk.Label(top, text="", font=("Helvetica", 12), fg="#222222", bg="white")
        self.status_label.pack(side=tk.LEFT, padx=16)

        input_frame = tk.LabelFrame(self.root, text="Deine Spracheingabe (Deutsch)", font=("Helvetica", 14), bg="white")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        self.input_text = tk.Text(input_frame, font=("Helvetica", 20), wrap=tk.WORD, height=6, bg="white", fg="black")
        self.input_text.pack(fill=tk.BOTH, expand=True)

        output_frame = tk.LabelFrame(self.root, text="Antwort der KI", font=("Helvetica", 14), bg="white")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.output_text = tk.Text(output_frame, font=("Helvetica", 20), wrap=tk.WORD, bg="white", fg="black")
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def _status(self, text: str):
        self._ui_queue.put(("status", text))

    def _append(self, widget_name: str, text: str, newline: bool = True):
        self._ui_queue.put((widget_name, (text, newline)))

    def _drain_ui_queue(self):
        widgets = {"input": self.input_text, "output": self.output_text}
        try:
            while True:
                kind, payload = self._ui_queue.get_nowait()
                if kind == "status":
                    self.status_label.config(text=payload)
                elif kind in widgets:
                    text, newline = payload
                    w = widgets[kind]
                    w.insert(tk.END, text + ("\n\n" if newline else ""))
                    w.see(tk.END)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_ui_queue)

    # ------------------------------------------------------------ Logik
    def _toggle_talk(self):
        if self._worker and self._worker.is_alive():
            self._stop_event.set()
            if self._mic_stream:
                self._mic_stream.stop()
            self.toggle_btn.config(text="Talk starten", bg="#2e7d32")
            self._status("Gestoppt.")
        else:
            self._stop_event.clear()
            self.toggle_btn.config(text="Talk stoppen", bg="#c62828")
            self._status("Hoere zu ...")
            self._worker = threading.Thread(target=self._run_recognition_loop, daemon=True)
            self._worker.start()

    def _run_recognition_loop(self):
        device = os.environ.get("MIC_DEVICE_INDEX")
        device = int(device) if device else None
        self._mic_stream = MicrophoneUtteranceStream(UtteranceConfig(), device=device)
        try:
            self._mic_stream.start()
        except Exception as exc:
            self._status(f"Fehler beim Mikrofonzugriff: {exc}")
            return

        for audio in self._mic_stream.utterances():
            if self._stop_event.is_set():
                break
            self._status("Erkenne ...")
            try:
                result = self._engine.transcribe(audio, language="de")
            except Exception as exc:
                self._status(f"Fehler bei der Spracherkennung: {exc}")
                continue

            if not result.text:
                self._status("Hoere zu ...")
                continue

            self._append("input", result.text)
            self._send_to_remote_ai(result.text)
            self._status("Hoere zu ...")

    def _send_to_remote_ai(self, prompt: str):
        self._status("Warte auf Antwort der KI ...")
        self._append("output", "> ", newline=False)
        try:
            for fragment in self._client.ask(prompt):
                self._append("output", fragment, newline=False)
        except Exception as exc:
            self._append("output", f"[Fehler bei der Verbindung zur KI: {exc}]")
            return
        self._append("output", "")


def main():
    root = tk.Tk()
    VoiceInputApp(root)
    root.mainloop()


if __name__ == "__main__":
    if "--list-devices" in sys.argv:
        for idx, name in list_input_devices():
            print(f"{idx}: {name}")
    else:
        main()
