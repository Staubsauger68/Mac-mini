#!/usr/bin/env bash
# Einmaliges Setup fuer Projekt B (Sprach-Eingabe fuer entfernte KI) auf dem Mac mini.
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v brew &> /dev/null; then
  echo "Homebrew wurde nicht gefunden. Installiere es zuerst von https://brew.sh" >&2
  exit 1
fi

echo "==> Installiere Systemabhaengigkeiten (portaudio, python-tk, ffmpeg) ..."
brew install portaudio python-tk@3.12 ffmpeg

echo "==> Erstelle virtuelle Python-Umgebung (.venv) ..."
python3 -m venv .venv
source .venv/bin/activate

echo "==> Installiere Python-Pakete ..."
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp config.example.env .env
  echo "==> .env angelegt. Bitte REMOTE_AI_URL / REMOTE_AI_MODEL eintragen!"
fi

cat <<'EOF'

Setup abgeschlossen.

Naechste Schritte:
  1. Auf dem Mac Studio / Windows-PC muss eine KI erreichbar sein, z.B.
     Ollama (https://ollama.com) oder LM Studio - im lokalen Netzwerk
     gestartet und fuer Netzwerkzugriff freigegeben.
  2. Trage in projekt-b-ki-eingabe/.env die Adresse dieses Rechners ein
     (REMOTE_AI_URL, REMOTE_AI_MODEL, ggf. REMOTE_AI_STYLE).
  3. macOS fragt beim ersten Start nach Mikrofon-Zugriff - bitte erlauben.
  4. Start:
       source .venv/bin/activate
       python3 voice_input.py

Mikrofon-Liste anzeigen:
       python3 voice_input.py --list-devices
EOF
