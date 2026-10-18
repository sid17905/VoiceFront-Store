"""S2 — JSON-LD must be valid JSON and must not terminate its script block."""
from __future__ import annotations

import json
import re

import pytest

from core.palette_engine import get_palette
from core.renderer import render

CATEGORIES = ["food", "apparel", "electronics", "pharmacy", "services"]
LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def spec(category="food", **overrides):
    base = {
        "shop_name": "Daily Bakery",
        "category": category,
        "description": "Sourdough and coffee",
        "products": [{"name": "Sourdough", "price": 180, "currency": "INR"}],
        "hours": ["Mon-Sat 8-8"],
        "contact": {"whatsapp": "9876543210", "phone": "9876543210"},
        "location": {"address": "12 Hill Rd", "city": "Mumbai", "state": "MH", "pincode": "400050"},
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize("category", CATEGORIES)
def test_jsonld_parses(category):
    html = render(category, spec(category), get_palette(category))
    blocks = LD_RE.findall(html)
    assert blocks, f"no JSON-LD block in {category}"
    data = json.loads(blocks[0])
    assert data["@context"] == "https://schema.org"
    assert data["name"] == "Daily Bakery"


@pytest.mark.parametrize("category", CATEGORIES)
def test_jsonld_type_is_category_specific(category):
    expected = {
        "food": "FoodEstablishment",
        "apparel": "ClothingStore",
        "electronics": "ElectronicsStore",
        "pharmacy": "PharmacyOrDrugstore",
        "services": "LocalBusiness",
    }[category]
    html = render(category, spec(category), get_palette(category))
    assert f'"@type": "{expected}"' in LD_RE.findall(html)[0]


def test_script_terminator_is_neutralised():
    html = render(
        "food",
        spec(description='</script><script>alert(1)</script>'),
        get_palette("food"),
    )
    blocks = LD_RE.findall(html)
    assert len(blocks) == 1, "payload terminated the JSON-LD block"
    data = json.loads(blocks[0])
    assert "</script>" in data["description"]


def test_jsonld_without_optional_fields():
    minimal = {"shop_name": "Bare", "category": "services", "products": []}
    html = render("services", minimal, get_palette("services"))
    data = json.loads(LD_RE.findall(html)[0])
    assert data["name"] == "Bare"
    assert "address" not in data
    assert "url" not in data
