"""S11 — rate limiting, body caps and API-key semantics."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "packages"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from common_utils.security import (  # noqa: E402
    DEFAULT_BODY_CAPS,
    DEFAULT_LIMITS,
    RateLimiter,
    SecurityMiddleware,
    require_api_key,
)


def make_app(**kwargs) -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityMiddleware, **kwargs)

    @app.post("/v1/nlp/extract")
    async def extract(request: Request):
        return {"ok": True}

    @app.get("/health")
    async def health():
        return {"status": "ok"}
    return app


# --- rate limiter ---------------------------------------------------------
def test_limiter_allows_up_to_limit():
    limiter = RateLimiter({"/x": 3}, window_seconds=60)
    assert all(limiter.hit("/x", "1.1.1.1", now=0) for _ in range(3))
    assert limiter.hit("/x", "1.1.1.1", now=0) is False


def test_limiter_is_per_ip():
    limiter = RateLimiter({"/x": 1}, window_seconds=60)
    assert limiter.hit("/x", "a", now=0) is True
    assert limiter.hit("/x", "b", now=0) is True
    assert limiter.hit("/x", "a", now=1) is False


def test_limiter_window_expires():
    limiter = RateLimiter({"/x": 1}, window_seconds=10)
    assert limiter.hit("/x", "a", now=0) is True
    assert limiter.hit("/x", "a", now=5) is False
    assert limiter.hit("/x", "a", now=11) is True


def test_unlisted_route_is_unlimited():
    limiter = RateLimiter({"/x": 1})
    assert all(limiter.hit("/health", "a", now=0) for _ in range(50))


# --- middleware -----------------------------------------------------------
def test_429_after_limit():
    client = TestClient(make_app(limits={"/v1/nlp/extract": 2}, window_seconds=60))
    assert client.post("/v1/nlp/extract").status_code == 200
    assert client.post("/v1/nlp/extract").status_code == 200
    r = client.post("/v1/nlp/extract")
    assert r.status_code == 429
    assert r.json()["error_code"] == "RATE_LIMITED"
    assert "Retry-After" in r.headers


def test_413_on_declared_oversize_body():
    client = TestClient(make_app(body_caps={"/v1/nlp/extract": 10}, limits={}))
    r = client.post("/v1/nlp/extract", content=b"x" * 100)
    assert r.status_code == 413
    assert r.json()["error_code"] == "REQUEST_TOO_LARGE"


def test_health_is_not_limited_or_capped():
    client = TestClient(make_app(limits={"/v1/nlp/extract": 1},
                                 body_caps={"/v1/nlp/extract": 1}))
    for _ in range(5):
        assert client.get("/health").status_code == 200


# --- api key --------------------------------------------------------------
def app_with_key() -> FastAPI:
    app = FastAPI()

    @app.post("/protected")
    async def protected(request: Request):
        require_api_key(request)
        return {"ok": True}
    return app


def test_key_allowed_when_configured(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "s3cret")
    monkeypatch.setenv("ENV", "dev")
    client = TestClient(app_with_key())
    assert client.post("/protected", headers={"X-API-Key": "s3cret"}).status_code == 200


def test_key_rejected_when_wrong(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "s3cret")
    monkeypatch.setenv("ENV", "dev")
    client = TestClient(app_with_key())
    assert client.post("/protected", headers={"X-API-Key": "nope"}).status_code == 401


def test_key_optional_in_dev(monkeypatch):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    monkeypatch.setenv("ENV", "dev")
    client = TestClient(app_with_key())
    assert client.post("/protected").status_code == 200


def test_key_required_in_production(monkeypatch):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    monkeypatch.setenv("ENV", "production")
    client = TestClient(app_with_key())
    assert client.post("/protected").status_code == 503


def test_default_limits_cover_every_route():
    for path in ("/v1/asr/transcribe", "/v1/nlp/extract", "/v1/layout/generate",
                 "/v1/layout/scrape", "/v1/qa/run", "/v1/publish"):
        assert path in DEFAULT_LIMITS
        assert path in DEFAULT_BODY_CAPS
