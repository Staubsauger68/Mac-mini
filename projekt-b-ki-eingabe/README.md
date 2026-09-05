# Projekt B: Deutsche Spracheingabe für eine entfernte KI

Der Mac mini erkennt deutsche Sprache über das Mikrofon (lokal per
Whisper, keine Cloud), schickt den erkannten Text als Prompt an eine KI,
die auf einem **anderen Rechner im Netzwerk** läuft (z.B. ein Mac Studio
oder ein Windows-PC), und zeigt die Antwort der KI hier auf dem Mac mini
an.

## Voraussetzungen

1. Auf dem Mac Studio / Windows-PC muss eine KI mit Netzwerk-Endpunkt
   laufen. Am einfachsten mit [Ollama](https://ollama.com) (kostenlos,
   für macOS und Windows):

   ```bash
   # Auf dem Mac Studio / Windows-PC:
   ollama pull llama3.1        # oder ein anderes Modell
   ```

   Damit Ollama auch aus dem Netzwerk (nicht nur localhost) erreichbar
   ist, muss es mit `OLLAMA_HOST=0.0.0.0` gestartet werden:

   - **macOS (Mac Studio)**:
     ```bash
     launchctl setenv OLLAMA_HOST "0.0.0.0"
     # Ollama-App/-Dienst danach neu starten
     ```
   - **Windows**: Systemumgebungsvariable `OLLAMA_HOST` auf `0.0.0.0`
     setzen (Systemsteuerung → Umgebungsvariablen), dann Ollama neu
     starten.

   Alternativ funktioniert auch [LM Studio](https://lmstudio.ai) (hat
   einen "Local Server" mit OpenAI-kompatiblem Endpunkt, in den
   Einstellungen auf "Serve on Network" stellen) oder jeder andere
   Server mit OpenAI-kompatibler `/v1/chat/completions`-API.

2. Beide Rechner müssen im selben Netzwerk sein und sich erreichen
   können (z.B. per `<rechnername>.local` über Bonjour/mDNS, das
   funktioniert zwischen Mac und Windows meist automatisch sobald
   Bonjour/"Apple Bonjour Services" installiert ist - bei Windows ggf.
   iTunes/Bonjour-Print-Services installieren, sonst die feste
   IP-Adresse verwenden).

3. Ein Mikrofon am Mac mini.

## Einrichtung

```bash
cd projekt-b-ki-eingabe
./setup.sh
```

Danach `.env` (aus `config.example.env` kopiert) ausfüllen:

```bash
REMOTE_AI_URL=http://mac-studio.local:11434/v1/chat/completions
REMOTE_AI_MODEL=llama3.1
REMOTE_AI_STYLE=openai
```

(Adresse/Modellname an deinen Aufbau anpassen - siehe Kommentare in
`config.example.env` für Ollama/LM Studio-Beispiele.)

## Start

```bash
source .venv/bin/activate
python3 voice_input.py
```

## Bedienung

1. **"Talk starten"** klicken.
2. Deutsch sprechen - der erkannte Text erscheint oben.
3. Der Text wird automatisch an die entfernte KI geschickt, die Antwort
   erscheint unten (wird live eingeblendet, sobald sie eintrifft).
4. **"Talk stoppen"** beendet die Aufnahme.

Der Gesprächsverlauf (Frage/Antwort) bleibt innerhalb einer laufenden
Sitzung erhalten, damit die KI Rückbezüge verstehen kann (App neu
starten setzt den Verlauf zurück).

## Konfiguration (`.env`)

| Variable | Bedeutung |
|---|---|
| `REMOTE_AI_URL` | Vollständige URL des Chat-Endpunkts auf dem anderen Rechner |
| `REMOTE_AI_MODEL` | Modellname, wie dort geladen/registriert |
| `REMOTE_AI_STYLE` | `openai` (Standard, OpenAI-kompatibel) oder `ollama` (natives Ollama-Protokoll) |
| `REMOTE_AI_API_KEY` | Nur nötig, falls der Server einen API-Key verlangt |
| `WHISPER_MODEL_SIZE` | `tiny`/`base`/`small`/`medium`/`large-v3` |
| `MIC_DEVICE_INDEX` | Optional: Mikrofon-Index |

## Troubleshooting

- **Verbindung schlägt fehl**: Erreichbarkeit testen mit
  `curl http://mac-studio.local:11434/api/tags` vom Mac mini aus. Falls
  das fehlschlägt, liegt es an Netzwerk/Firewall/`OLLAMA_HOST`, nicht an
  diesem Programm.
- **Firewall auf dem Windows-PC**: Eingehende Verbindungen auf dem
  genutzten Port (z.B. 11434 oder 1234) in der Windows-Firewall
  erlauben.
- **Falsches Mikrofon**: `python3 voice_input.py --list-devices`.
