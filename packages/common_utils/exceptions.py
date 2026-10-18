"""
Shared exception hierarchy for VoiceStorefront services.
Per common_references.md: every service raises from this base — never a bare Exception,
or the API gateway can't map it to a meaningful HTTP status for the frontend.

`status_code` is carried on the exception rather than guessed in the handler
(Q2): a missing version is a 404, a malformed request is a 400, an upstream
failure is a 502/503. Defaults to 500 so an unclassified error stays a server
fault instead of being disguised.
"""


class VoiceStorefrontError(Exception):
    """Base class for every service-raised error in this system."""

    status_code: int = 500

    def __init__(self, error_code: str, message: str, status_code: int | None = None):
        self.error_code = error_code
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(f"{error_code}: {message}")

    def to_dict(self) -> dict:
        # Matches the shared error body shape in api_contracts.md:
        # { "error_code": "string", "message": "string" }
        return {"error_code": self.error_code, "message": self.message}


class AsrError(VoiceStorefrontError):
    """asr-service errors (ASR_UNSUPPORTED_FORMAT, ASR_TRANSCRIPTION_FAILED)."""
    status_code = 502


class SchemaValidationError(VoiceStorefrontError):
    """nlp-service errors — malformed input only, not a schema that failed validation
    (that's a normal 200 with is_valid: false, per api_contracts.md)."""
    status_code = 422


class LayoutError(VoiceStorefrontError):
    """layout-service errors (LAYOUT_NO_TEMPLATE_MATCH, LAYOUT_RENDER_FAILED)."""
    status_code = 500


class QaViolationError(VoiceStorefrontError):
    """qa-service errors — reserved for pipeline failure (Playwright crash, FAISS
    unreachable). Violations *found* during a normal run is not this — that's a 200."""
    status_code = 500


class PublishError(VoiceStorefrontError):
    """publish-service errors (PUBLISH_QA_NOT_PASSED, PUBLISH_S3_FAILED)."""
    status_code = 409
