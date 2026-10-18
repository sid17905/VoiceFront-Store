import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def test_publish_error_mapping():
    from services.publish_service.main import app
    client = TestClient(app)
    # Test invalid version id / non-existent bundle triggering 404/409/422
    response = client.post("/v1/publish", json={"version_id": "nonexistent-version-12345"})
    # Should be 401/403 due to API key or 404/409 for missing bundle
    assert response.status_code in (401, 403, 404, 409, 422)
