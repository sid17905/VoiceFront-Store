"""
services/publish-service/main.py — FastAPI entrypoint.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
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

app = FastAPI(title="publish-service", version="0.1.0")
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
