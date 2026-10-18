"""ASR contract proofs (A1, A2, A6).

Live mode must fail with 503 rather than returning a fabricated transcript.
Simulator mode must be explicit and labelled.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

SERVICE = Path(__file__).resolve().parents[1]  # services/asr-service
if str(SERVICE) not in sys.path:
    sys.path.insert(0, str(SERVICE))

# Reuse the service app loading pattern used by the existing integration test.
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location("asr_main_under_test", SERVICE / "main.py")
module = importlib.util.module_from_spec(spec)
sys.modules["asr_main_under_test"] = module
spec.loader.exec_module(module)
client = TestClient(module.app)

WAV = b"RIFF" + (36).to_bytes(4, "little") + b"WAVEfmt " + b"\x10\x00\x00\x00" + b"\x00" * 60


def post(data: bytes, name="clip.wav", ctype="audio/wav", params=None):
    return client.post(
        "/v1/asr/transcribe",
        files={"audio_file": (name, io.BytesIO(data), ctype)},
        data=params or {},
    )


def test_simulator_mode_is_explicit(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "simulator")
    r = post(WAV)
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "simulator"
    assert body["warning"]


def test_live_mode_without_key_is_503(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "live")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    r = post(WAV, params={"language": "en"})
    assert r.status_code == 503
    assert r.json()["detail"]["error_code"] == "ASR_UPSTREAM_UNAVAILABLE"


def test_live_mode_never_returns_canned_text(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "live")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    r = post(WAV)
    assert "Tony's Pizza Kitchen" not in r.text


def test_rejects_non_audio_payload(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "simulator")
    r = post(b"this is not audio at all, really", name="x.wav")
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "ASR_UNSUPPORTED_FORMAT"


def test_rejects_empty_payload(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "simulator")
    r = post(b"", name="empty.wav")
    assert r.status_code == 400


def test_rejects_unsupported_extension(monkeypatch):
    monkeypatch.setenv("ASR_MODE", "simulator")
    r = post(WAV, name="notes.txt", ctype="text/plain")
    assert r.status_code == 400


@pytest.mark.parametrize("name,ctype", [
    ("a.mp3", "audio/mpeg"),
    ("a.ogg", "audio/ogg"),
    ("a.webm", "audio/webm"),
])
def test_accepts_supported_types_in_simulator(monkeypatch, name, ctype):
    monkeypatch.setenv("ASR_MODE", "simulator")
    magic = {"a.mp3": b"ID3" + b"\x00" * 60,
             "a.ogg": b"OggS" + b"\x00" * 60,
             "a.webm": b"\x1a\x45\xdf\xa3" + b"\x00" * 60}[name]
    r = post(magic, name=name, ctype=ctype)
    assert r.status_code == 200
