"""services/qa-service/main.py — FastAPI entrypoint."""

from __future__ import annotations

import os
import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers.qa import router as qa_router

try:
    from common_utils.exceptions import QaViolationError
except ImportError:
    class QaViolationError(Exception):
        def __init__(self, error_code: str, message: str):
            self.error_code = error_code
            self.message = message
            super().__init__(f"{error_code}: {message}")

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","service":"qa-service","request_id":"%(request_id)s","message":"%(message)s"}',
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

try:
    from common_utils.security import SecurityMiddleware
    _security_available = True
except ImportError:  # pragma: no cover - standalone fallback
    SecurityMiddleware = None  # type: ignore[assignment]
    _security_available = False

app = FastAPI(
    title="qa-service",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENV", "dev") != "production" else None,
    redoc_url=None,
)

if _security_available:
    app.add_middleware(SecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

app.include_router(qa_router)


@app.middleware("http")
async def request_id_and_logging(request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    start = time.monotonic()
    response = await call_next(request)
    ms = round((time.monotonic() - start) * 1000, 1)
    logging.info(
        f"method={request.method} path={request.url.path} status={response.status_code} ms={ms}",
        extra={"request_id": request_id},
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(QaViolationError)
async def qa_violation_error_handler(request: Request, exc: QaViolationError):
    return JSONResponse(status_code=500, content=exc.to_dict() if hasattr(exc, "to_dict") else {
        "error_code": exc.error_code, "message": exc.message,
    })


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", extra={"request_id": "?"})
    return JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred."})


@app.get("/health")
def health():
    from pathlib import Path
    rules_dir = Path(__file__).parent.parent.parent / "data" / "constraint-rules"
    return {
        "status": "ok",
        "service": "qa-service",
        "version": "2.0.0",
        "rules_loaded": len(list(rules_dir.glob("*.json"))) if rules_dir.exists() else 0,
    }
