import pytest
from fastapi.testclient import TestClient
import sys
import importlib.util
from pathlib import Path

nlp_service_dir = Path(__file__).resolve().parents[2]
if str(nlp_service_dir) not in sys.path:
    sys.path.insert(0, str(nlp_service_dir))
root_dir = Path(__file__).resolve().parents[4]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

for mod in ["main", "routers", "core"]:
    if mod in sys.modules:
        del sys.modules[mod]

spec = importlib.util.spec_from_file_location("nlp_main", nlp_service_dir / "main.py")
module = importlib.util.module_from_spec(spec)
sys.modules["nlp_main"] = module
spec.loader.exec_module(module)
app = module.app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "nlp-service"


def test_extract_food_store():
    prompt = "Create a store called Tony's Pizza Cafe. We sell Margherita Pizza for Rs 299 and Garlic Bread at 149. Contact us at 9876543210."
    response = client.post("/v1/nlp/extract", json={"prompt": prompt})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    spec = data["storefront_spec"]
    assert "Pizza" in spec["shop_name"] or "Tony" in spec["shop_name"]
    assert spec["category"] == "food"
    assert len(spec["products"]) > 0


def test_extract_apparel_store():
    prompt = "Welcome to Urban Stitch Boutique. We sell Cotton Shirts for 799 and Denim Jeans for 1299. Located in Bangalore."
    response = client.post("/v1/nlp/extract", json={"prompt": prompt})
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    spec = data["storefront_spec"]
    assert spec["category"] == "apparel"


def test_extract_empty_fails():
    response = client.post("/v1/nlp/extract", json={"prompt": ""})
    assert response.status_code == 400
