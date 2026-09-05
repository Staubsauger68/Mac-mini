# Projekt A: Echtzeit-Übersetzer

Verwandelt den Mac mini in ein Dolmetscher-Werkzeug: Mikrofon an, auf
"Talk starten" klicken, sprechen. Die Sprache wird per
[Whisper](https://github.com/openai/whisper) (lokal, ohne Cloud) erkannt.

- Deutsch wird groß in einem eigenen Feld angezeigt.
- Sobald eine zweite Sprache erkannt wird, merkt sich die App diese
  Sprache automatisch. Text in der zweiten Sprache wird im Original
  **und** in deutscher Übersetzung angezeigt (via [DeepL](https://www.deepl.com)).
- Deutscher Text wird zusätzlich in die erkannte zweite Sprache übersetzt,
  sobald diese feststeht.

## Voraussetzungen

- macOS mit [Homebrew](https://brew.sh)
- Ein angeschlossenes Mikrofon
- Ein **DeepL API-Key** (kein Benutzername/Passwort!). Den bekommst du,
  wenn du dich in deinen DeepL-Account einloggst, unter
  **Konto → API-Keys**. Falls dein Account ein kostenloser
  "DeepL API Free"-Account ist, endet der Key auf `:fx` und die
  Bibliothek stellt automatisch auf den Free-Endpunkt um - das ist
  bereits im Code berücksichtigt (das `deepl`-Paket erkennt das selbst).

> Hinweis zu deinem DeepL-Zugang: Das Login `werbung@bartylla.de` mit
> Passwort ist der **Web-Login** für die DeepL-Website, nicht der
> API-Key. Für die Automatisierung hier wird zwingend ein API-Key
> benötigt (Klartext-Passwörter sollten grundsätzlich nie in
> Konfigurationsdateien landen). Bitte logg dich einmal unter
> https://www.deepl.com/your-account/keys ein und kopiere den Key.

## Einrichtung

```bash
cd projekt-a-uebersetzer
./setup.sh
```

Das Skript installiert Systemabhängigkeiten via Homebrew, legt eine
virtuelle Python-Umgebung an und installiert alle Python-Pakete. Danach
`.env` (aus `config.example.env` kopiert) mit deinem DeepL API-Key
befüllen.

## Start

```bash
source .venv/bin/activate
python3 translator.py
```

Beim allerersten Start lädt Whisper das Modell herunter (ein paar
hundert MB, je nach `WHISPER_MODEL_SIZE`) - das dauert einmalig etwas.

macOS fragt beim ersten Mikrofonzugriff nach einer Berechtigung -
unbedingt erlauben (sonst unter **Systemeinstellungen → Datenschutz &
Sicherheit → Mikrofon** nachtragen).

## Bedienung

1. Auf **"Talk starten"** klicken.
2. Sprechen - Sätze werden erkannt, sobald eine kurze Sprechpause
   erkannt wird (ca. 0,7 Sekunden). Das ist der übliche Ansatz für
   Whisper-basierte Nahezu-Echtzeit-Erkennung (echte
   Wort-für-Wort-Streaming-Erkennung unterstützt Whisper technisch
   nicht).
3. Deutscher Text erscheint oben, die zweite Sprache (Original +
   Übersetzung) unten.
4. **"Talk stoppen"** beendet die Aufnahme.

## Konfiguration (`.env`)

| Variable | Bedeutung |
|---|---|
| `DEEPL_API_KEY` | Dein DeepL API-Key |
| `WHISPER_MODEL_SIZE` | `tiny`/`base`/`small`/`medium`/`large-v3` - größer = genauer, aber langsamer |
| `MIC_DEVICE_INDEX` | Optional: Mikrofon-Index, falls mehrere Geräte angeschlossen sind |

Mikrofone auflisten:

```bash
python3 translator.py --list-devices
```

## Tuning / Troubleshooting

- **Erkennung zu langsam**: kleineres Modell (`tiny`/`base`) verwenden.
- **Erkennung bricht Sätze zu früh/spät ab**: `silence_ms_to_stop` in
  `common/audio_stream.py` (`UtteranceConfig`) anpassen.
- **Falsches Mikrofon**: `--list-devices` nutzen und `MIC_DEVICE_INDEX`
  setzen.
- **DeepL-Fehler "Wrong endpoint"**: passiert nicht, das `deepl`-Paket
  wählt Free/Pro-Endpunkt automatisch anhand des Keys.
