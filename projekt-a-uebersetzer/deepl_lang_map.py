"""Mapping von Whisper-Sprachcodes (ISO 639-1) auf DeepL-Sprachcodes.

Whisper liefert z.B. "en", "fr", "de", "tr". DeepL erwartet fuer manche
Sprachen spezifischere Codes (z.B. "EN-US" als Zielsprache). Fuer die
Quellsprache reicht bei DeepL meist der einfache Code.
"""
from __future__ import annotations

# Zielsprachen-Codes, bei denen DeepL eine Variante verlangt.
TARGET_OVERRIDES = {
    "en": "EN-US",
    "pt": "PT-PT",
    "zh": "ZH",
}

# Von DeepL unterstuetzte Sprachen (Auszug der gaengigsten). Whisper kann
# theoretisch mehr Sprachen erkennen als DeepL uebersetzen kann - in dem
# Fall wird nur der Originaltext ohne Uebersetzung angezeigt.
DEEPL_SUPPORTED = {
    "bg", "cs", "da", "de", "el", "en", "es", "et", "fi", "fr", "hu", "id",
    "it", "ja", "ko", "lt", "lv", "nb", "nl", "pl", "pt", "ro", "ru", "sk",
    "sl", "sv", "tr", "uk", "zh",
}


def to_deepl_source(whisper_lang: str) -> str | None:
    code = whisper_lang.lower()
    if code not in DEEPL_SUPPORTED:
        return None
    return code.upper()


def to_deepl_target(whisper_lang: str) -> str | None:
    code = whisper_lang.lower()
    if code not in DEEPL_SUPPORTED:
        return None
    return TARGET_OVERRIDES.get(code, code.upper())
