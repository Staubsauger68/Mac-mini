#!/usr/bin/env python3
"""Projekt A: Echtzeit-Uebersetzungswerkzeug.

Nimmt ueber das Mikrofon Sprache auf, erkennt sie per Whisper
(automatische Spracherkennung), und uebersetzt zwischen Deutsch und
einer zweiten, automatisch erkannten Sprache via DeepL. Ergebnisse
werden gross in einem Fenster angezeigt.

Start/Stop ueber den "Talk starten/stoppen"-Knopf in der GUI.
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox

import deepl
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.audio_stream import MicrophoneUtteranceStream, UtteranceConfig, list_input_devices  # noqa: E402
from common.whisper_engine import WhisperEngine  # noqa: E402

from deepl_lang_map import to_deepl_source, to_deepl_target  # noqa: E402

load_dotenv(Path(__file__).resolve().parent / ".env")

GERMAN = "de"


class TranslatorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Whisper Echtzeit-Uebersetzer")
        self.root.geometry("1100x900")
        self.root.minsize(700, 700)

        self.second_lang: str | None = None
        self._ui_queue: "queue.Queue[tuple]" = queue.Queue()
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._mic_stream: MicrophoneUtteranceStream | None = None

        self._build_ui()

        deepl_key = os.environ.get("DEEPL_API_KEY", "").strip()
        if not deepl_key:
            messagebox.showerror(
                "DeepL API-Key fehlt",
                "Bitte DEEPL_API_KEY in projekt-a-uebersetzer/.env eintragen.\n"
                "Den Key findest du in deinem DeepL-Account unter 'Konto -> API-Keys'.",
            )
        self._deepl = deepl.Translator(deepl_key) if deepl_key else None

        model_size = os.environ.get("WHISPER_MODEL_SIZE", "small")
        self._status(f"Lade Whisper-Modell '{model_size}' ...")
        self._engine = WhisperEngine(model_size=model_size)
        self._status("Bereit. Klicke auf 'Talk starten'.")

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

        big_font = tkfont.Font(family="Helvetica", size=30, weight="bold")
        small_font = tkfont.Font(family="Helvetica", size=18)

        caption_font = ("Helvetica", 11, "bold")

        de_frame = tk.LabelFrame(self.root, text="Deutsch", font=("Helvetica", 14), bg="white")
        de_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))
        tk.Label(de_frame, text="Deutsche Sprache + Übersetzung der zweiten Sprache ins Deutsche",
                 font=caption_font, bg="white", fg="#666666").pack(anchor="w")
        self.de_text = tk.Text(de_frame, font=big_font, wrap=tk.WORD, height=6, bg="white", fg="black")
        self.de_text.pack(fill=tk.BOTH, expand=True)

        other_frame = tk.LabelFrame(self.root, text="Zweite Sprache (automatisch erkannt)", font=("Helvetica", 14), bg="white")
        other_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        tk.Label(other_frame, text="Original in der zweiten Sprache",
                 font=caption_font, bg="white", fg="#666666").pack(anchor="w")
        self.other_original_text = tk.Text(other_frame, font=big_font, wrap=tk.WORD, height=4, bg="white", fg="black")
        self.other_original_text.pack(fill=tk.BOTH, expand=True)
        tk.Label(other_frame, text="Übersetzung des deutschen Textes in die zweite Sprache",
                 font=caption_font, bg="white", fg="#666666").pack(anchor="w")
        self.other_translation_text = tk.Text(other_frame, font=small_font, wrap=tk.WORD, height=4, bg="white", fg="#444444")
        self.other_translation_text.pack(fill=tk.BOTH, expand=True)

    def _status(self, text: str):
        self._ui_queue.put(("status", text))

    def _append(self, widget_name: str, text: str):
        self._ui_queue.put((widget_name, text))

    def _drain_ui_queue(self):
        widgets = {
            "de": self.de_text,
            "other_original": self.other_original_text,
            "other_translation": self.other_translation_text,
        }
        try:
            while True:
                kind, payload = self._ui_queue.get_nowait()
                if kind == "status":
                    self.status_label.config(text=payload)
                elif kind in widgets:
                    w = widgets[kind]
                    w.insert(tk.END, payload + "\n\n")
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
            self._clear_texts()
            self._stop_event.clear()
            self.toggle_btn.config(text="Talk stoppen", bg="#c62828")
            self._status("Hoere zu ...")
            self._worker = threading.Thread(target=self._run_recognition_loop, daemon=True)
            self._worker.start()

    def _clear_texts(self):
        self.second_lang = None
        self.de_text.delete("1.0", tk.END)
        self.other_original_text.delete("1.0", tk.END)
        self.other_translation_text.delete("1.0", tk.END)

    def _run_recognition_loop(self):
        device = os.environ.get("MIC_DEVICE_INDEX")
        device = int(device) if device else None
        self._mic_stream = MicrophoneUtteranceStream(UtteranceConfig(), device=device)
        try:
            self._mic_stream.start()
        except Exception as exc:  # z.B. fehlende Mikrofon-Berechtigung
            self._status(f"Fehler beim Mikrofonzugriff: {exc}")
            return

        for audio in self._mic_stream.utterances():
            if self._stop_event.is_set():
                break
            self._status("Erkenne ...")
            try:
                result = self._engine.transcribe(audio, language=None)
            except Exception as exc:
                self._status(f"Fehler bei der Spracherkennung: {exc}")
                continue

            if not result.text:
                self._status("Hoere zu ...")
                continue

            self._handle_utterance(result.text, result.language)
            self._status("Hoere zu ...")

    def _handle_utterance(self, text: str, language: str):
        if language == GERMAN:
            self._append("de", text)
            if self.second_lang and self._deepl:
                self._translate_and_show(text, GERMAN, self.second_lang, "other_translation")
        else:
            if self.second_lang is None:
                self.second_lang = language
                self._status(f"Zweite Sprache erkannt: {language}")
            self._append("other_original", text)
            if self._deepl:
                self._translate_and_show(text, language, GERMAN, "de")

    def _translate_and_show(self, text: str, source_lang: str, target_lang: str, widget_name: str):
        deepl_source = to_deepl_source(source_lang)
        deepl_target = to_deepl_target(target_lang)
        if not deepl_source or not deepl_target:
            return
        try:
            result = self._deepl.translate_text(
                text, source_lang=deepl_source, target_lang=deepl_target
            )
            self._append(widget_name, f"({source_lang} -> {target_lang}) {result.text}")
        except Exception as exc:
            self._status(f"DeepL-Fehler: {exc}")


def main():
    root = tk.Tk()
    TranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    if "--list-devices" in sys.argv:
        for idx, name in list_input_devices():
            print(f"{idx}: {name}")
    else:
        main()
