from __future__ import annotations

import os
import logging
import time
from core.normalize import normalize_transcript

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = "The audio describes a retail shop or storefront, including its name, items for sale, prices, location, and opening hours."
PLACEHOLDER_KEYS = {"", "mock", "placeholder", "your_groq_api_key_here"}


def _simulator_response(language: str) -> dict:
    simulated_text = "Welcome to Tony's Pizza Kitchen. We serve fresh Margherita Pizza for Rs 299 and Pasta for Rs 249. Open every day 10 AM to 10 PM. Contact 9876543210."
    return {
        "transcript": normalize_transcript(simulated_text),
        "language": language,
        "confidence": 0.98,
        "mode": "simulator",
        "warning": "GROQ_API_KEY not configured — mock transcription active. Set GROQ_API_KEY for real audio processing.",
        "segments": [{"id": 0, "start": 0.0, "end": 4.5, "text": simulated_text}],
    }


async def transcribe_audio(
    file_bytes: bytes,
    filename: str,
    language: str = "en",
    api_key: str | None = None,
) -> dict:
    key = api_key or os.getenv("GROQ_API_KEY", "")

    if key.strip() in PLACEHOLDER_KEYS:
        logger.warning("ASR running in simulator mode — GROQ_API_KEY not set")
        return _simulator_response(language)

    try:
        from groq import Groq
    except ImportError:
        logger.error("groq package not installed — falling back to simulator")
        return _simulator_response(language)

    try:
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _call_groq():
            client = Groq(api_key=key)
            return client.audio.transcriptions.create(
                file=(filename, file_bytes),
                model="whisper-large-v3",
                prompt=DEFAULT_PROMPT,
                response_format="verbose_json",
                language=language,
                temperature=0.0,
            )

        t0 = time.monotonic()
        response = _call_groq()
        ms = round((time.monotonic() - t0) * 1000, 1)
        logger.info(f"Groq Whisper transcription complete in {ms}ms")

        return {
            "transcript": normalize_transcript(getattr(response, "text", "")),
            "language": language,
            "confidence": 0.95,
            "mode": "live",
            "segments": getattr(response, "segments", []),
        }

    except Exception as exc:
        logger.error(f"Groq Whisper failed after retries: {exc} — falling back to simulator")
        result = _simulator_response(language)
        result["warning"] = f"Groq API error: {exc}. Using simulator fallback."
        return result
