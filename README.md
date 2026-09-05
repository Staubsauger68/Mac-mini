# Mac-mini – Whisper-Setup

Zwei eigenständige Sprach-Werkzeuge für den Mac mini, beide basieren auf
lokaler Spracherkennung mit [Whisper](https://github.com/openai/whisper)
(über [faster-whisper](https://github.com/SYSTRAN/faster-whisper)) und
haben ein einfaches Tkinter-Fenster als Anzeige.

| Projekt | Zweck |
|---|---|
| [`projekt-a-uebersetzer/`](projekt-a-uebersetzer/README.md) | Echtzeit-Dolmetscher: Mikrofon → Text (groß angezeigt) → Übersetzung Deutsch ⇄ automatisch erkannte zweite Sprache, via DeepL |
| [`projekt-b-ki-eingabe/`](projekt-b-ki-eingabe/README.md) | Deutsche Spracheingabe für eine KI auf einem anderen Rechner (Mac Studio / Windows-PC) im Netzwerk, Antwort wird hier angezeigt |

## Wichtiger Hinweis zur Ausführung

Dieser Code wurde in einer Cloud-Sandbox erstellt (Claude Code on the
web) – **ohne Zugriff auf dein tatsächliches Mikrofon, deine Netzwerk-
geräte oder dein DeepL-Konto**. Die eigentliche Einrichtung
(`./setup.sh` in den jeweiligen Projektordnern, Eintragen der API-Keys,
Mikrofon-Berechtigung erteilen) musst du **einmalig lokal auf deinem
Mac mini** ausführen:

```bash
git clone <dieses-repo>
cd Mac-mini
cd projekt-a-uebersetzer && ./setup.sh   # Projekt A einrichten
cd ../projekt-b-ki-eingabe && ./setup.sh # Projekt B einrichten
```

Danach jeweils die `.env`-Datei im Projektordner mit deinen echten
Zugangsdaten befüllen (siehe die READMEs der Projekte). Zugangsdaten
werden **nie** ins Git-Repository eingecheckt (siehe `.gitignore`) -
insbesondere nicht dein DeepL-Web-Passwort, das ohnehin nicht für die
API verwendet wird (dafür braucht es einen API-Key, siehe
[projekt-a-uebersetzer/README.md](projekt-a-uebersetzer/README.md)).

## Gemeinsamer Code

`common/` enthält geteilten Code für beide Projekte:

- `audio_stream.py` – Mikrofonaufnahme mit Sprachaktivitäts-Erkennung
  (VAD), segmentiert kontinuierliches Audio in einzelne Sprachabschnitte.
- `whisper_engine.py` – dünner Wrapper um `faster-whisper`.

## Voraussetzungen (beide Projekte)

- macOS mit [Homebrew](https://brew.sh)
- Xcode Command Line Tools (`xcode-select --install`, falls noch nicht
  installiert - wird von manchen Python-Paketen beim Bauen benötigt)
- Ein angeschlossenes Mikrofon
- Python 3 (wird von `setup.sh` über Homebrew mitinstalliert)

Details, Konfiguration und Bedienung stehen in den jeweiligen
Projekt-READMEs verlinkt oben.
