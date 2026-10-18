"""Shared security primitives: API keys, rate limiting and body caps.

Implemented once here so the five services cannot drift (invariant I-A5's
spirit applied to security). Deliberately dependency-free.

Limitations, stated rather than hidden:
- The rate limiter is per-process and in-memory. With N replicas the effective
  limit is N x the configured value. A shared store (Redis) is future work and
  is named as such in the report.
- `ENV=production` requires INTERNAL_API_KEY to be set; otherwise protected
  routes fail closed at request time.
"""
from __future__ import annotations

import hmac
import os
import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

DEFAULT_LIMITS: dict[str, int] = {
    "/v1/asr/transcribe": 10,
    "/v1/nlp/extract": 30,
    "/v1/layout/generate": 60,
    "/v1/layout/scrape": 5,
    "/v1/qa/run": 10,
    "/v1/publish": 5,
}

DEFAULT_BODY_CAPS: dict[str, int] = {
    "/v1/asr/transcribe": 25 * 1024 * 1024,
    "/v1/nlp/extract": 64 * 1024,
    "/v1/layout/generate": 512 * 1024,
    "/v1/layout/scrape": 8 * 1024,
    "/v1/qa/run": 2 * 1024 * 1024,
    "/v1/publish": 8 * 1024,
}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """Fixed-window limiter keyed by (route, client ip)."""

    def __init__(self, limits: dict[str, int] | None = None, window_seconds: int = 60):
        self.limits = limits or DEFAULT_LIMITS
        self.window = window_seconds
        self._hits: dict[tuple[str, str], list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def hit(self, path: str, ip: str, now: float | None = None) -> bool:
        """Record a hit. Returns False when the limit is exceeded."""
        limit = self.limits.get(path)
        if limit is None:
            return True
        now = time.monotonic() if now is None else now
        cutoff = now - self.window
        with self._lock:
            bucket = [t for t in self._hits[(path, ip)] if t > cutoff]
            if len(bucket) >= limit:
                self._hits[(path, ip)] = bucket
                return False
            bucket.append(now)
            self._hits[(path, ip)] = bucket
        return True


class SecurityMiddleware(BaseHTTPMiddleware):
    """Applies a body cap and a rate limit to configured routes."""

    def __init__(self, app, *, limits: dict[str, int] | None = None,
                 body_caps: dict[str, int] | None = None, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(limits, window_seconds)
        self.body_caps = body_caps or DEFAULT_BODY_CAPS

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        cap = self.body_caps.get(path)
        if cap is not None:
            declared = request.headers.get("content-length")
            if declared is not None:
                try:
                    if int(declared) > cap:
                        return JSONResponse(
                            status_code=413,
                            content={"error_code": "REQUEST_TOO_LARGE",
                                     "message": f"body exceeds {cap} bytes"},
                        )
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content={"error_code": "INVALID_CONTENT_LENGTH",
                                 "message": "Content-Length is not a number"},
                    )

        if path in (self.limiter.limits or {}):
            if not self.limiter.hit(path, _client_ip(request)):
                return JSONResponse(
                    status_code=429,
                    content={"error_code": "RATE_LIMITED",
                             "message": "too many requests; retry later"},
                    headers={"Retry-After": str(self.limiter.window)},
                )

        return await call_next(request)


def require_api_key(request: Request) -> None:
    """FastAPI dependency for protected routes (publish, scrape).

    - If INTERNAL_API_KEY is unset and ENV != production: allowed (dev).
    - If unset and ENV == production: 503, so a misconfigured deploy fails
      closed rather than exposing the route.
    """
    expected = os.getenv("INTERNAL_API_KEY", "").strip()
    if not expected:
        if os.getenv("ENV", "dev") == "production":
            raise HTTPException(status_code=503,
                                detail={"error_code": "AUTH_NOT_CONFIGURED",
                                        "message": "INTERNAL_API_KEY is not set"})
        return
    supplied = request.headers.get("x-api-key", "")
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401,
                            detail={"error_code": "UNAUTHORIZED",
                                    "message": "missing or invalid API key"})
