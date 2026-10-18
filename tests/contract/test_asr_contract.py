"""ASR contract tests."""
from __future__ import annotations

import importlib.util
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"
sys.path.insert(0, str(ROOT / "packages"))


def load_app(service: str):
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


WAV = b"RIFF" + (36).to_bytes(4, "little") + b"WAVEfmt " + b"\x10\x00\x00\x00" + b"\x00" * 60


def test_asr_health_shape():
    body = load_app("asr-service").get("/health").json()
    assert body["service"] == "asr-service"
    assert body["groq_api"] in ("live", "simulator")


def test_asr_simulator_is_labelled(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "simulator")
    r = load_app("asr-service").post(
        "/v1/asr/transcribe",
        files={"audio_file": ("a.wav", io.BytesIO(WAV), "audio/wav")},
    )
    assert r.status_code == 200
    assert r.json()["mode"] == "simulator"


def test_asr_live_without_key_is_503(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "live")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    r = load_app("asr-service").post(
        "/v1/asr/transcribe",
        files={"audio_file": ("a.wav", io.BytesIO(WAV), "audio/wav")},
    )
    assert r.status_code == 503
    assert r.json()["detail"]["error_code"] == "ASR_UPSTREAM_UNAVAILABLE"
