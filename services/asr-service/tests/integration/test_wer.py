import pytest
from fastapi.testclient import TestClient
import sys
import io
import importlib.util
from pathlib import Path

asr_service_dir = Path(__file__).resolve().parents[2]
if str(asr_service_dir) not in sys.path:
    sys.path.insert(0, str(asr_service_dir))

# Clean up cached conflicting namespaces
for mod in ["main", "routers", "core"]:
    if mod in sys.modules:
        del sys.modules[mod]

spec = importlib.util.spec_from_file_location("asr_main", asr_service_dir / "main.py")
module = importlib.util.module_from_spec(spec)
sys.modules["asr_main"] = module
spec.loader.exec_module(module)
app = module.app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_transcribe_endpoint():
    dummy_wav = io.BytesIO(b"RIFF4\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x10\x00\x00\x00" + b"\x00" * 16)
    dummy_wav.name = "test.wav"

    response = client.post(
        "/v1/asr/transcribe",
        files={"audio_file": ("test.wav", dummy_wav, "audio/wav")},
        data={"language": "en"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert data["language"] == "en"
    assert data["confidence"] > 0
