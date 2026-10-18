"""S5/S6/S7/S8/S9 — rendering invariants."""
from __future__ import annotations

import importlib
import json
import sys

import pytest

from core.palette_engine import get_palette
from core.renderer import render

CATEGORIES = ["food", "apparel", "electronics", "pharmacy", "services"]


def spec(**overrides):
    base = {
        "shop_name": "Test Store",
        "category": "food",
        "description": "A shop",
        "products": [{"name": "Item", "price": 100, "currency": "INR"}],
        "hours": [],
        "contact": {},
        "location": None,
    }
    base.update(overrides)
    return base


# --- S5 -------------------------------------------------------------------
def test_no_fingerprint_global():
    html = render("food", spec(), get_palette("food"))
    assert "__voicefront_fingerprint" not in html
    assert "navigator.userAgent" not in html


# --- S6 -------------------------------------------------------------------
@pytest.mark.parametrize("category", CATEGORIES)
def test_no_invented_whatsapp(category):
    html = render(category, spec(category=category), get_palette(category))
    assert "wa.me/9876543210" not in html
    assert "9876543210" not in html


def test_whatsapp_renders_when_present():
    html = render("food", spec(contact={"whatsapp": "9123456789"}), get_palette("food"))
    assert "wa.me/9123456789" in html


def test_no_third_party_image_hosts():
    for category in CATEGORIES:
        html = render(category, spec(category=category), get_palette(category))
        assert "images.unsplash.com" not in html
        assert "https://images." not in html


# --- S7 -------------------------------------------------------------------
def test_fallback_returns_complete_document():
    html = render("missing-template", spec(), get_palette("food"))
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert "Test Store" in html


# --- S8 -------------------------------------------------------------------
@pytest.mark.parametrize("price", [None, "", "Ask", "₹180", 0, 180, 12.5])
def test_price_never_raises(price):
    html = render(
        "food",
        spec(products=[{"name": "Thing", "price": price, "currency": "INR"}]),
        get_palette("food"),
    )
    assert "Thing" in html


def test_price_none_reads_ask():
    html = render(
        "food",
        spec(products=[{"name": "Thing", "price": None, "currency": "INR"}]),
        get_palette("food"),
    )
    assert "Ask for price" in html


@pytest.mark.parametrize("location", [
    {"address": "12 Hill Rd", "city": "Mumbai", "state": "MH", "pincode": "400050"},
    {"city": "Pune"},
    {},
    None,
])
def test_location_renders_without_raw_text(location):
    html = render("food", spec(location=location), get_palette("food"))
    assert "raw_text" not in html
    if location and location.get("city"):
        assert location["city"] in html


def test_currency_symbols():
    usd = render(
        "food",
        spec(products=[{"name": "Coffee", "price": 5, "currency": "USD"}]),
        get_palette("food"),
    )
    assert "$5" in usd


# --- S9 -------------------------------------------------------------------
def test_empty_template_dir_falls_back(monkeypatch):
    monkeypatch.setenv("LAYOUT_TEMPLATE_DIR", "")
    import core.renderer as renderer
    importlib.reload(renderer)
    html = renderer.render("food", spec(), get_palette("food"))
    assert "<!DOCTYPE html>" in html
    monkeypatch.delenv("LAYOUT_TEMPLATE_DIR", raising=False)
    importlib.reload(renderer)


def test_whitespace_template_dir_falls_back(monkeypatch):
    monkeypatch.setenv("LAYOUT_TEMPLATE_DIR", "   ")
    import core.renderer as renderer
    importlib.reload(renderer)
    assert renderer._TEMPLATE_DIR.exists()
    monkeypatch.delenv("LAYOUT_TEMPLATE_DIR", raising=False)
    importlib.reload(renderer)
