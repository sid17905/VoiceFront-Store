"""Audio upload validation (A2).

Checks MIME/extension *and* magic bytes, and enforces the size cap before the
whole file is read into memory.
"""
from __future__ import annotations

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

ALLOWED_MIME_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/mpeg",
    "audio/mp3",
    "audio/m4a",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm",
    "audio/ogg",
    "application/octet-stream",
}

ALLOWED_EXTENSIONS = (".wav", ".mp3", ".m4a", ".webm", ".ogg", ".mp4")

# Leading bytes of the formats we accept. `ftyp` sits at offset 4 for MP4/M4A.
_MAGIC = (
    (0, b"RIFF"),        # WAV
    (0, b"ID3"),         # MP3 with ID3 tag
    (0, b"\xff\xfb"),    # MP3 frame
    (0, b"\xff\xf3"),
    (0, b"\xff\xf2"),
    (0, b"OggS"),        # OGG
    (0, b"fLaC"),        # FLAC
    (4, b"ftyp"),        # MP4 / M4A
)


class InvalidAudio(ValueError):
    pass


def looks_like_audio(content: bytes) -> bool:
    if len(content) < 12:
        return False
    for offset, signature in _MAGIC:
        if content[offset:offset + len(signature)] == signature:
            return True
    # WebM/Matroska
    return content[:4] == b"\x1a\x45\xdf\xa3"


def validate_audio_upload(filename: str | None, content_type: str | None,
                          content_length: int | None) -> None:
    """Cheap checks that need no body. Raises InvalidAudio."""
    if not filename:
        raise InvalidAudio("filename is missing")

    if content_length is not None and content_length > MAX_FILE_SIZE_BYTES:
        raise InvalidAudio(f"file exceeds {MAX_FILE_SIZE_BYTES} bytes")

    ctype = (content_type or "application/octet-stream").lower()
    if ctype not in ALLOWED_MIME_TYPES and not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise InvalidAudio(f"unsupported audio type: {ctype}")


def validate_audio_content(content: bytes) -> None:
    """Body checks that need the bytes. Raises InvalidAudio."""
    if not content:
        raise InvalidAudio("audio payload is empty")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise InvalidAudio(f"file exceeds {MAX_FILE_SIZE_BYTES} bytes")
    if not looks_like_audio(content):
        raise InvalidAudio("payload does not look like a supported audio file")
