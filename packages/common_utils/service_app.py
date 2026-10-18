"""Shared FastAPI application factory (A2).

Before this existed, CORS, the request-id middleware, the JSON log formatter and
the exception handlers were copy-pasted into five `main.py` files and had
drifted. The formatter declared `%(request_id)s` with no filter supplying it, so
any record logged without `extra={"request_id": ...}` — including uvicorn's own
records — raised `KeyError: 'request_id'` while logging.

This module is the single place those concerns live.
"""
from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from .exceptions import VoiceStorefrontError
except ImportError:  # pragma: no cover - standalone import path
    from common_utils.exceptions import VoiceStorefrontError


class _ContextFilter(logging.Filter):
    """Guarantees every record has the fields the formatter references."""

    def __init__(self, service: str):
        super().__init__()
        self.service = service

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        if not hasattr(record, "service"):
            record.service = self.service
        return True


LOG_FORMAT = (
    '{"time":"%(asctime)s","level":"%(levelname)s","service":"%(service)s",'
    '"request_id":"%(request_id)s","message":"%(message)s"}'
)


def configure_logging(service: str, level: str | None = None) -> None:
    """Install one handler with the JSON formatter and the context filter."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(_ContextFilter(service))

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel((level or os.getenv("LOG_LEVEL", "INFO")).upper())

    # uvicorn installs its own handlers; make them propagate to ours instead of
    # formatting with the bare "%(message)s" default.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers[:] = []
        logger.propagate = True


def create_app(
    name: str,
    version: str,
    *,
    cors: bool = True,
    docs: bool | None = None,
    health_extra: Callable[[], dict] | None = None,
) -> FastAPI:
    """Build a service app.

    `health_extra` lets a service add fields (mode, rule count, model name) to
    the shared /health body. Register a second /health route instead and the
    factory's route wins, silently hiding the extra fields.
    """
    configure_logging(name)

    app = FastAPI(
        title=name,
        version=version,
        docs_url=("/docs" if (docs if docs is not None else os.getenv("ENV", "dev") != "production") else None),
        redoc_url=None,
    )

    if cors:
        origins = os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080"
        ).split(",")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[o.strip() for o in origins if o.strip()],
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "Authorization", "X-Request-ID", "X-API-Key"],
        )

    @app.middleware("http")
    async def request_context(request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        started = time.monotonic()
        response = await call_next(request)
        elapsed = round((time.monotonic() - started) * 1000, 1)
        logging.getLogger(name).info(
            "method=%s path=%s status=%s ms=%s",
            request.method, request.url.path, response.status_code, elapsed,
            extra={"request_id": request_id},
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(VoiceStorefrontError)
    async def known_error(request: Request, exc: VoiceStorefrontError):
        status = getattr(exc, "status_code", 500)
        return JSONResponse(status_code=status, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def unknown_error(request: Request, exc: Exception):
        logging.getLogger(name).error(
            "unhandled error: %s", type(exc).__name__, extra={"request_id": "-"}
        )
        return JSONResponse(
            status_code=500,
            content={"error_code": "INTERNAL_ERROR",
                     "message": "An unexpected error occurred."},
        )

    @app.get("/health")
    async def health() -> dict:
        body = {"status": "ok", "service": name, "version": version}
        if health_extra is not None:
            try:
                body.update(health_extra())
            except Exception:  # a broken probe must still return a body
                body["health_extra_error"] = True
        return body

    return app
