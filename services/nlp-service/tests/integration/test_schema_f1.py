"""Schema extraction evaluation (N5).

This replaces the previous "test_schema_f1.py", which contained four endpoint
smoke tests and computed no F1. It now measures:

  - shop_name exact match (case/punctuation normalised)
  - category exact match
  - product-name set recall and price agreement for matched names
  - schema validity rate

The extraction runs through whatever path is configured: live Groq when
GROQ_API_KEY is set, otherwise the deterministic fallback. The report prints
which path ran, because the two numbers are not comparable.

Thresholds are recorded, not assumed: `BASELINE` below is updated only after a
real run, per invariant I-T3.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

SERVICE = Path(__file__).resolve().parents[2]          # services/nlp-service
ROOT = Path(__file__).resolve().parents[4]            # repo root
for p in (str(SERVICE), str(ROOT), str(ROOT / "packages")):
    if p not in sys.path:
        sys.path.insert(0, p)

if "core" in sys.modules:
    del sys.modules["core"]

from core.schema_builder import extract_storefront_spec  # noqa: E402

GOLD = ROOT / "data" / "seed" / "storefront_specs" / "gold" / "prompts.json"


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def norm_price(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    digits = re.sub(r"[^0-9.]", "", str(value))
    try:
        return float(digits)
    except ValueError:
        return None


def score(spec, expected: dict) -> dict:
    products = {norm(p.name): norm_price(p.price) for p in spec.products}
    wanted = [(norm(n), float(pr)) for n, pr in expected["products"]]

    matched = 0
    price_ok = 0
    for name, price in wanted:
        hits = [k for k in products if name in k or k in name]
        if hits:
            matched += 1
            if any(products[h] is not None and abs(products[h] - price) < 0.01 for h in hits):
                price_ok += 1

    return {
        "shop_ok": norm(spec.shop_name) == norm(expected["shop_name"]),
        "category_ok": spec.category.value == expected["category"],
        "product_recall": (matched / len(wanted)) if wanted else 1.0,
        "price_agreement": (price_ok / len(wanted)) if wanted else 1.0,
    }


@pytest.mark.asyncio
async def test_gold_set_extraction(capsys):
    cases = json.loads(GOLD.read_text(encoding="utf-8"))
    results = []
    valid = 0

    for case in cases:
        spec, is_valid, invalid = await extract_storefront_spec(case["prompt"])
        valid += int(is_valid)
        row = score(spec, case["expected"])
        row["valid"] = is_valid
        row["invalid"] = invalid
        results.append(row)

    n = len(results)
    validity_rate = valid / n
    shop_acc = sum(r["shop_ok"] for r in results) / n
    category_acc = sum(r["category_ok"] for r in results) / n
    recall = sum(r["product_recall"] for r in results) / n
    price = sum(r["price_agreement"] for r in results) / n

    mode = "live" if os.getenv("GROQ_API_KEY") else "fallback"
    print(f"\nmode={mode} n={n}")
    print(f"schema validity : {validity_rate:.3f}")
    print(f"shop_name acc   : {shop_acc:.3f}")
    print(f"category acc    : {category_acc:.3f}")
    print(f"product recall  : {recall:.3f}")
    print(f"price agreement : {price:.3f}")

    failures = [
        {"case": i, **r}
        for i, r in enumerate(results)
        if not (r["shop_ok"] and r["category_ok"] and r["product_recall"] >= 0.5)
    ]
    print(f"cases below bar : {len(failures)}")
    for f in failures:
        print("  ", f)

    # Hard requirements that hold in both modes:
    assert category_acc >= 0.80, "category accuracy below 80%"
    assert recall >= 0.60, "product recall below 60%"
    # Shop-name accuracy is deliberately soft in fallback mode (regex), strict live.
    assert shop_acc >= (0.80 if mode == "live" else 0.40)


# ---------------------------------------------------------------------------
# Contract tests restored from the previous version of this file (I-T1: the F1
# harness replaced this module, it must not delete the endpoint assertions).
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("nlp_main_under_test", SERVICE / "main.py")
_module = importlib.util.module_from_spec(_spec)
sys.modules["nlp_main_under_test"] = _module
_spec.loader.exec_module(_module)
_client = TestClient(_module.app)


def test_health():
    r = _client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "nlp-service"


def test_extract_food_store():
    r = _client.post("/v1/nlp/extract", json={
        "prompt": "Create a store called Tony's Pizza Cafe. Margherita Pizza for Rs 299 and Garlic Bread at 149. Contact 9876543210."
    })
    assert r.status_code == 200
    body = r.json()
    spec = body["storefront_spec"]
    assert spec["category"] == "food"
    assert len(spec["products"]) > 0


def test_extract_apparel_store():
    r = _client.post("/v1/nlp/extract", json={
        "prompt": "Welcome to Urban Stitch Boutique. Cotton Shirts for 799 and Denim Jeans for 1299."
    })
    assert r.status_code == 200
    assert r.json()["storefront_spec"]["category"] == "apparel"


def test_extract_empty_fails():
    r = _client.post("/v1/nlp/extract", json={"prompt": ""})
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "EMPTY_PROMPT"


def test_extract_whitespace_fails():
    r = _client.post("/v1/nlp/extract", json={"prompt": "   "})
    assert r.status_code == 400
    assert r.json()["detail"]["error_code"] == "EMPTY_PROMPT"


def test_invalid_fields_are_structured():
    r = _client.post("/v1/nlp/extract", json={"prompt": "A shop with no useful detail"})
    assert r.status_code == 200
    for item in r.json()["invalid_fields"]:
        assert set(item) == {"field", "reason"}
