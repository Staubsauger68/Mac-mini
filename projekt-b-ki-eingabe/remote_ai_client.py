"""Client fuer eine KI, die auf einem anderen Rechner im Netzwerk laeuft
(z.B. Ollama oder LM Studio auf einem Mac Studio oder Windows-PC).

Unterstuetzt zwei Betriebsarten (REMOTE_AI_STYLE):

  "openai" (Standard): OpenAI-kompatible Chat-Completions-API.
      Funktioniert mit Ollama (>= 0.7, Endpoint z.B.
      http://<host>:11434/v1/chat/completions), LM Studio
      (http://<host>:1234/v1/chat/completions), text-generation-webui
      mit OpenAI-Erweiterung, vLLM, etc.

  "ollama": natives Ollama-Protokoll
      (http://<host>:11434/api/chat).

Beide Varianten werden gestreamt, damit die Antwort nicht erst am Ende
komplett erscheint.
"""
from __future__ import annotations

import json
from collections.abc import Iterator

import requests


class RemoteAIClient:
    def __init__(self, url: str, model: str, api_key: str | None = None, style: str = "openai", timeout: int = 120):
        self.url = url
        self.model = model
        self.api_key = api_key
        self.style = style
        self.timeout = timeout
        self._history: list[dict] = []

    def reset_history(self):
        self._history = []

    def ask(self, prompt: str) -> Iterator[str]:
        """Schickt den Prompt an die entfernte KI und liefert die Antwort
        stueckweise (Generator von Text-Fragmenten)."""
        self._history.append({"role": "user", "content": prompt})
        if self.style == "ollama":
            full = yield from self._ask_ollama()
        else:
            full = yield from self._ask_openai()
        self._history.append({"role": "assistant", "content": full})

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key.lower() not in ("", "not-needed"):
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _ask_openai(self):
        payload = {
            "model": self.model,
            "messages": self._history,
            "stream": True,
        }
        full_text = ""
        with requests.post(self.url, json=payload, headers=self._headers(), stream=True, timeout=self.timeout) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                data = line[len("data:"):].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if delta:
                    full_text += delta
                    yield delta
        return full_text

    def _ask_ollama(self):
        payload = {
            "model": self.model,
            "messages": self._history,
            "stream": True,
        }
        full_text = ""
        with requests.post(self.url, json=payload, headers=self._headers(), stream=True, timeout=self.timeout) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("message", {}).get("content", "")
                if delta:
                    full_text += delta
                    yield delta
                if chunk.get("done"):
                    break
        return full_text
