#!/usr/bin/env bash
# Erstellt eine doppelklickbare Startdatei auf dem Schreibtisch fuer
# Projekt B (Sprach-Eingabe fuer entfernte KI). Einmalig ausfuehren:
#   bash Desktop-Verknuepfung-erstellen.sh
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/Desktop/KI-Spracheingabe-starten.command"

cat > "$TARGET" << EOF
#!/bin/bash
cd "$PROJECT_DIR" || { echo "Projektordner nicht gefunden: $PROJECT_DIR"; read -p "Enter zum Schliessen"; exit 1; }
source .venv/bin/activate
python3 voice_input.py
EOF

chmod +x "$TARGET"
echo "Fertig! Auf dem Schreibtisch liegt jetzt: KI-Spracheingabe-starten.command"
echo "Einfach doppelklicken zum Starten."
