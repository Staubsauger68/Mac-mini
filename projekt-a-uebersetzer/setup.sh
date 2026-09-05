#!/usr/bin/env bash
# Einmaliges Setup fuer Projekt A (Echtzeit-Uebersetzer) auf dem Mac mini.
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
  echo "==> .env angelegt. Bitte DEEPL_API_KEY in projekt-a-uebersetzer/.env eintragen!"
fi

cat <<'EOF'

Setup abgeschlossen.

Naechste Schritte:
  1. Trage deinen DeepL API-Key in projekt-a-uebersetzer/.env ein
     (DEEPL_API_KEY=...). Den Key gibt es im DeepL-Account unter
     "Konto" -> "API-Keys" (NICHT Benutzername/Passwort).
  2. macOS fragt beim ersten Start nach Mikrofon-Zugriff fuer Terminal/
     Python - bitte erlauben (Systemeinstellungen -> Datenschutz &
     Sicherheit -> Mikrofon).
  3. Start:
       source .venv/bin/activate
       python3 translator.py

Mikrofon-Liste anzeigen (falls das falsche Geraet gewaehlt wird):
       python3 translator.py --list-devices
EOF
