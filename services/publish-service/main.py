"""
services/publish-service/main.py — FastAPI entrypoint.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.responses import JSONResponse

from routers.publish import router as publish_router

try:
    from common_utils.exceptions import PublishError
except ImportError:  # pragma: no cover
    class PublishError(Exception):
        def __init__(self, error_code: str, message: str):
            self.error_code = error_code
            self.message = message
            super().__init__(f"{error_code}: {message}")

try:
    from common_utils.security import SecurityMiddleware
    _security_available = True
except ImportError:  # pragma: no cover - standalone fallback
    SecurityMiddleware = None  # type: ignore[assignment]
    _security_available = False

app = FastAPI(title="publish-service", version="0.1.0")

# Add CORS middleware
ALLOW_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOW_ORIGINS],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"])

if _security_available:
    app.add_middleware(SecurityMiddleware)
app.include_router(publish_router)


@app.exception_handler(PublishError)
async def publish_error_handler(request: Request, exc: PublishError):
    # api_contracts.md: 409 PublishError (PUBLISH_QA_NOT_PASSED | PUBLISH_S3_FAILED)
    return JSONResponse(status_code=409, content=exc.to_dict() if hasattr(exc, "to_dict") else {
        "error_code": exc.error_code, "message": exc.message,
    })


@app.get("/health")
def health():
    return {"status": "ok", "service": "publish-service"}
