from __future__ import annotations

import os

from fastapi import FastAPI

from routers.transcribe import router as transcribe_router

try:
    from common_utils.security import SecurityMiddleware
    _security_available = True
except ImportError:  # pragma: no cover - standalone fallback
    SecurityMiddleware = None  # type: ignore[assignment]
    _security_available = False

app = FastAPI(
    title="VoiceFront ASR Service",
    description="Speech Recognition and Transcription Service",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENV", "dev") != "production" else None,
    redoc_url=None,
)

if _security_available:
    app.add_middleware(SecurityMiddleware)

app.include_router(transcribe_router, prefix="/v1/asr", tags=["asr"])


@app.get("/health")
async def health():
    key = os.getenv("GROQ_API_KEY", "").strip()
    placeholder = {"", "mock", "placeholder", "your_groq_api_key_here"}
    return {
        "status": "ok",
        "service": "asr-service",
        "version": "2.0.0",
        "groq_api": "live" if key not in placeholder else "simulator",
    }
