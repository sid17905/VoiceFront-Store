"""
Shared exception hierarchy for VoiceStorefront services.
Per common_references.md: every service raises from this base — never a bare Exception,
or the API gateway can't map it to a meaningful HTTP status for the frontend.
"""


class VoiceStorefrontError(Exception):
    """Base class for every service-raised error in this system."""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"{error_code}: {message}")

    def to_dict(self) -> dict:
        # Matches the shared error body shape in api_contracts.md:
        # { "error_code": "string", "message": "string" }
        return {"error_code": self.error_code, "message": self.message}


class AsrError(VoiceStorefrontError):
    """asr-service errors (ASR_UNSUPPORTED_FORMAT, ASR_TRANSCRIPTION_FAILED)."""


class SchemaValidationError(VoiceStorefrontError):
    """nlp-service errors — malformed input only, not a schema that failed validation
    (that's a normal 200 with is_valid: false, per api_contracts.md)."""


class LayoutError(VoiceStorefrontError):
    """layout-service errors (LAYOUT_NO_TEMPLATE_MATCH, LAYOUT_RENDER_FAILED)."""


class QaViolationError(VoiceStorefrontError):
    """qa-service errors — reserved for pipeline failure (Playwright crash, FAISS
    unreachable). Violations *found* during a normal run is not this — that's a 200."""


class PublishError(VoiceStorefrontError):
    """publish-service errors (PUBLISH_QA_NOT_PASSED, PUBLISH_S3_FAILED)."""
