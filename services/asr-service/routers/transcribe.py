from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from core.validation import validate_audio_file
from core.whisper_engine import transcribe_audio

router = APIRouter()


class TranscriptionResponse(BaseModel):
    transcript: str
    language: str
    confidence: float
    segments: list = []


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_endpoint(
    audio_file: UploadFile = File(...),
    shop_id: Optional[str] = Form(None),
    language: Optional[str] = Form("en"),
) -> TranscriptionResponse:
    is_valid, err_msg = validate_audio_file(audio_file)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "ASR_UNSUPPORTED_FORMAT", "message": err_msg},
        )

    try:
        content = await audio_file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "ASR_EMPTY_FILE", "message": "Audio file payload is empty"},
            )

        result = await transcribe_audio(
            file_bytes=content,
            filename=audio_file.filename or "audio.wav",
            language=language or "en",
        )

        return TranscriptionResponse(
            transcript=result["transcript"],
            language=result["language"],
            confidence=result["confidence"],
            segments=result.get("segments", []),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error_code": "ASR_TRANSCRIPTION_FAILED", "message": str(exc)},
        )
