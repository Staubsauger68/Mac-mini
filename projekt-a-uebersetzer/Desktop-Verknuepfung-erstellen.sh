#!/usr/bin/env bash
# Erstellt eine doppelklickbare Startdatei auf dem Schreibtisch fuer
# Projekt A (Uebersetzer). Einmalig ausfuehren:
#   bash Desktop-Verknuepfung-erstellen.sh
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="$HOME/Desktop/Uebersetzer-starten.command"

cat > "$TARGET" << EOF
#!/bin/bash
cd "$PROJECT_DIR" || { echo "Projektordner nicht gefunden: $PROJECT_DIR"; read -p "Enter zum Schliessen"; exit 1; }
source .venv/bin/activate
python3 translator.py
EOF

chmod +x "$TARGET"
echo "Fertig! Auf dem Schreibtisch liegt jetzt: Uebersetzer-starten.command"
echo "Einfach doppelklicken zum Starten."
