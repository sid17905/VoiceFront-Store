from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from core.validation import (
    MAX_FILE_SIZE_BYTES,
    InvalidAudio,
    validate_audio_content,
    validate_audio_upload,
)
from core.whisper_engine import AsrUnavailable, mode, transcribe_audio

router = APIRouter()


class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float
    segments: list = []
    mode: str = "live"          # live | simulator  (A1)
    warning: str | None = None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_endpoint(
    request: Request,
    audio_file: UploadFile = File(...),
    shop_id: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
) -> TranscriptionResponse:
    declared = request.headers.get("content-length")
    try:
        content_length = int(declared) if declared is not None else None
    except ValueError:
        content_length = None
    if content_length is not None and content_length > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail={"error_code": "ASR_FILE_TOO_LARGE",
                    "message": f"audio exceeds {MAX_FILE_SIZE_BYTES} bytes"},
        )

    try:
        validate_audio_upload(audio_file.filename, audio_file.content_type, content_length)
    except InvalidAudio as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "ASR_UNSUPPORTED_FORMAT", "message": str(exc)},
        )

    content = await audio_file.read()
    try:
        validate_audio_content(content)
    except InvalidAudio as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "ASR_UNSUPPORTED_FORMAT", "message": str(exc)},
        )

    try:
        result = await transcribe_audio(
            file_bytes=content,
            filename=audio_file.filename or "audio.wav",
            language=language or None,
        )
    except AsrUnavailable as exc:
        # A1: never fabricate a transcript. The caller must know ASR is down.
        raise HTTPException(
            status_code=503,
            detail={"error_code": "ASR_UPSTREAM_UNAVAILABLE", "message": str(exc)},
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail={"error_code": "ASR_TRANSCRIPTION_FAILED",
                    "message": "transcription failed"},
        )

    return TranscriptionResponse(
        transcript=result["transcript"],
        language=result.get("language", "en"),
        confidence=float(result.get("confidence", 0.0)),
        segments=result.get("segments", []),
        mode=result.get("mode", mode()),
        warning=result.get("warning"),
    )
