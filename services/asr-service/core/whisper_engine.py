"""ASR engine — live Whisper via Groq, or an explicit simulator.

Modes (A1):
  ASR_MODE=live        (default) real transcription; upstream failures raise
                       AsrUnavailable -> HTTP 503. Never fabricates content.
  ASR_MODE=simulator   returns a fixed transcript and says so in `mode`.

The previous behaviour returned the canned transcript on *any* failure with
HTTP 200, which meant an API outage silently produced fake menu data
downstream. That path no longer exists.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time

from core.normalize import normalize_transcript

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = (
    "The audio describes a retail shop or storefront, including its name, "
    "items for sale, prices, location, and opening hours."
)
PLACEHOLDER_KEYS = {"", "mock", "placeholder", "your_groq_api_key_here"}

SIMULATED_TEXT = (
    "Welcome to Tony's Pizza Kitchen. We serve fresh Margherita Pizza for "
    "Rs 299 and Pasta for Rs 249. Open every day 10 AM to 10 PM. "
    "Contact 9876543210."
)


class AsrUnavailable(RuntimeError):
    """Raised when live transcription cannot be performed."""


def mode() -> str:
    value = os.getenv("ASR_MODE", "live").strip().lower()
    return value if value in {"live", "simulator"} else "live"


def _key() -> str:
    return os.getenv("GROQ_API_KEY", "").strip()


def _simulator_response(language: str) -> dict:
    return {
        "transcript": normalize_transcript(SIMULATED_TEXT),
        "language": language,
        "confidence": 0.0,
        "mode": "simulator",
        "segments": [{"id": 0, "start": 0.0, "end": 4.5, "text": SIMULATED_TEXT}],
        "warning": "ASR_MODE=simulator: this transcript is synthetic.",
    }


def _live_call(file_bytes: bytes, filename: str, language: str | None) -> dict:
    """Synchronous Groq call — executed in a worker thread (A4)."""
    try:
        from groq import Groq
    except ImportError as exc:
        raise AsrUnavailable("groq package is not installed") from exc

    key = _key()
    if key in PLACEHOLDER_KEYS:
        raise AsrUnavailable("GROQ_API_KEY is not configured")

    client = Groq(api_key=key, timeout=60.0)

    kwargs = {
        "file": (filename, file_bytes),
        "model": os.getenv("GROQ_ASR_MODEL", "whisper-large-v3"),
        "prompt": DEFAULT_PROMPT,
        "response_format": "verbose_json",
        "temperature": 0.0,
    }
    if language:
        kwargs["language"] = language

    response = client.audio.transcriptions.create(**kwargs)
    text = getattr(response, "text", "") or ""
    # A6: use the language Whisper reports, not the value we asked for.
    detected = getattr(response, "language", None) or language or "en"
    return {
        "transcript": normalize_transcript(text),
        "language": detected,
        "confidence": 0.0,   # Whisper does not expose a calibrated score
        "mode": "live",
        "segments": getattr(response, "segments", []) or [],
    }


async def transcribe_audio(
    file_bytes: bytes,
    filename: str,
    language: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Transcribe audio. Raises AsrUnavailable when live mode cannot proceed."""
    if api_key:
        os.environ["GROQ_API_KEY"] = api_key

    if mode() == "simulator":
        return _simulator_response(language or "en")

    if not file_bytes:
        raise AsrUnavailable("empty audio payload")

    from tenacity import (
        retry,
        retry_if_exception_type,
        stop_after_attempt,
        wait_exponential,
    )

    try:
        from groq import APIConnectionError, APITimeoutError, RateLimitError
    except ImportError as exc:  # pragma: no cover
        raise AsrUnavailable("groq package is not installed") from exc

    call = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError)),
        reraise=True,
    )(_live_call)

    started = time.monotonic()
    try:
        result = await asyncio.to_thread(call, file_bytes, filename, language)
    except Exception as exc:
        logger.error("live transcription failed: %s", type(exc).__name__)
        raise AsrUnavailable("transcription service unavailable") from exc

    logger.info("transcription complete in %dms", int((time.monotonic() - started) * 1000))
    return result
