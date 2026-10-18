from __future__ import annotations


def detect_language(audio_bytes: bytes, default: str = "en") -> str:
    """Modular language detection.
    In V2 English baseline, defaults strictly to English.
    Provides pluggable interface for future IndicLID integrations.
    """
    return default
