"""API contract tests (T5).

These assert the wire contracts in docs/procedure/api_contracts.md, including
the error paths the audit found untested. Each service is loaded in isolation
through the same loader the e2e suite uses, because all five define a
top-level `core` namespace package.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"
sys.path.insert(0, str(ROOT / "packages"))


def load_app(service: str):
    """Load services/<service>/main.py as an isolated module."""
    service_dir = SERVICES / service
    sys.path[:] = [p for p in sys.path if str(Path(p).resolve()) not in
                   {str(d.resolve()) for d in SERVICES.iterdir() if d.is_dir()}]
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "packages"))
    sys.path.insert(0, str(service_dir))
    for name in list(sys.modules):
        if name in ("core", "routers", "main") or name.startswith(("core.", "routers.")):
            del sys.modules[name]
    import importlib
    importlib.invalidate_caches()
    spec = importlib.util.spec_from_file_location(f"{service}_main", service_dir / "main.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"{service}_main"] = module
    spec.loader.exec_module(module)
    return TestClient(module.app)


# ---------------------------------------------------------------------------
# NLP
# ---------------------------------------------------------------------------

def test_nlp_health_shape():
    client = load_app("nlp-service")
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["service"] == "nlp-service"
    assert body["groq_api"] in ("live", "heuristic-fallback")


def test_nlp_empty_prompt_is_400_empty_prompt():
    client = load_app("nlp-service")
    r = client.post("/v1/nlp/extract", json={"prompt": ""})
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "EMPTY_PROMPT"


def test_nlp_accepts_transcript_for_backward_compatibility():
    client = load_app("nlp-service")
    r = client.post("/v1/nlp/extract", json={
        "transcript": "Bakery named Crust and Crumb, sourdough 180"
    })
    assert r.status_code == 200
    assert r.json()["storefront_spec"]["shop_name"]


def test_nlp_invalid_fields_shape():
    client = load_app("nlp-service")
    r = client.post("/v1/nlp/extract", json={"prompt": "a shop"})
    body = r.json()
    assert isinstance(body["invalid_fields"], list)
    for item in body["invalid_fields"]:
        assert set(item) == {"field", "reason"}


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def test_layout_generate_shape():
    client = load_app("layout-service")
    r = client.post("/v1/layout/generate", json={
        "shop_name": "Contract Shop",
        "category": "food",
        "products": [{"name": "Tea", "price": 20}],
        "contact": {"whatsapp": "9876543210"},
    })
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"template_id", "html"}
    assert body["template_id"] == "food"


def test_layout_unknown_category_is_422():
    client = load_app("layout-service")
    r = client.post("/v1/layout/generate", json={
        "shop_name": "X", "category": "not-a-category", "products": [],
    })
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def test_qa_invalid_request_is_400():
    client = load_app("qa-service")
    r = client.post("/v1/qa/run", json={})
    assert r.status_code == 400
    assert r.json()["error_code"] == "QA_INVALID_REQUEST"


def test_qa_missing_version_is_404():
    client = load_app("qa-service")
    r = client.post("/v1/qa/run", json={"version_id": "no-such-fixture"})
    assert r.status_code == 404
    assert r.json()["error_code"] == "QA_VERSION_NOT_FOUND"


def test_qa_traversal_is_400():
    client = load_app("qa-service")
    r = client.post("/v1/qa/run", json={"version_id": "../../etc/passwd"})
    assert r.status_code == 400
    assert r.json()["error_code"] == "QA_INVALID_REQUEST"


def test_qa_report_has_pass_rule_and_repair_fields():
    client = load_app("qa-service")
    r = client.post("/v1/qa/run", json={"html": "<html><body><main><h1>x</h1></main></body></html>"})
    # QA needs a browser; if it cannot run, it must say so, never fabricate a pass.
    if r.status_code == 200:
        report = r.json()["qa_report"]
        assert report["pass_rule"] == "no-critical"
        assert "critical_violations" in report
        assert "repaired_html" in r.json()
    else:
        assert r.status_code >= 500


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

def test_publish_missing_bundle_is_404_or_gated(monkeypatch):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    monkeypatch.setenv("ENV", "dev")
    client = load_app("publish-service")
    r = client.post("/v1/publish", json={"version_id": "nonexistent-version-12345"})
    assert r.status_code in (404, 409, 503)
    body = r.json()
    assert "error_code" in body or "detail" in body


def test_publish_traversal_is_rejected(monkeypatch):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    monkeypatch.setenv("ENV", "dev")
    client = load_app("publish-service")
    r = client.post("/v1/publish", json={"version_id": "../secrets"})
    assert r.status_code in (400, 404, 409)
