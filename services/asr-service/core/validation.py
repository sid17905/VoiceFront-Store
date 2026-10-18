from __future__ import annotations

from fastapi import UploadFile

ALLOWED_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/m4a",
    "audio/mp4",
    "audio/webm",
    "audio/ogg",
    "application/octet-stream",
}

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


def validate_audio_file(file: UploadFile) -> tuple[bool, str | None]:
    if not file.filename:
        return False, "Filename is missing"

    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_MIME_TYPES:
        valid_extensions = (".wav", ".mp3", ".m4a", ".webm", ".ogg")
        if not file.filename.lower().endswith(valid_extensions):
            return False, f"Unsupported audio format: {content_type}. Allowed: wav, mp3, m4a, webm, ogg."

    return True, None
