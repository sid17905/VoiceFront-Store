"""One Groq client for every service (A1).

Three call paths existed: the SDK from ASR, the SDK from NLP, and a raw
`httpx.post` from QA that read the key at import time and ignored GROQ_MODEL.
This module is the only place a key, model or client is chosen.

Models:
  GROQ_MODEL         chat extraction        (default openai/gpt-oss-120b)
  GROQ_REPAIR_MODEL  QA repair              (default llama-3.1-8b-instant)
  GROQ_ASR_MODEL     transcription          (default whisper-large-v3)

Key handling: `api_key()` raises GroqNotConfigured when the key is absent or a
known placeholder, so callers choose their own fallback explicitly instead of
receiving a client that fails at call time.
"""
from __future__ import annotations

import os
from functools import lru_cache

PLACEHOLDER_KEYS = {"", "mock", "placeholder", "your_groq_api_key_here"}

DEFAULT_MODELS = {
    "chat": "openai/gpt-oss-120b",
    "repair": "llama-3.1-8b-instant",
    "asr": "whisper-large-v3",
}


class GroqNotConfigured(RuntimeError):
    """Raised when no usable GROQ_API_KEY is present."""


def api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key.lower() in PLACEHOLDER_KEYS:
        raise GroqNotConfigured("GROQ_API_KEY is not configured")
    return key


def is_configured() -> bool:
    try:
        api_key()
        return True
    except GroqNotConfigured:
        return False


def model(kind: str = "chat") -> str:
    if kind == "chat":
        return os.getenv("GROQ_MODEL", DEFAULT_MODELS["chat"])
    if kind == "repair":
        return os.getenv("GROQ_REPAIR_MODEL",
                         os.getenv("GROQ_MODEL", DEFAULT_MODELS["repair"]))
    if kind == "asr":
        return os.getenv("GROQ_ASR_MODEL", DEFAULT_MODELS["asr"])
    raise ValueError(f"unknown model kind: {kind!r}")


@lru_cache(maxsize=1)
def client():
    """Return a process-wide Groq client. Raises GroqNotConfigured."""
    try:
        from groq import Groq
    except ImportError as exc:  # pragma: no cover
        raise GroqNotConfigured("groq package is not installed") from exc
    return Groq(api_key=api_key(), timeout=60.0)


def reset() -> None:
    """Clear the cached client (tests and key rotation)."""
    client.cache_clear()
