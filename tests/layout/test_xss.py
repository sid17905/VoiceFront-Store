"""S1 — autoescaping must hold for .jinja2 templates and the fallback."""
from __future__ import annotations

import pytest

from core.palette_engine import get_palette
from core.renderer import render

PAYLOAD = '<script>alert(1)</script>'
ATTR_PAYLOAD = '"><img src=x onerror=alert(1)>'


def spec(**overrides):
    base = {
        "shop_name": "Safe Store",
        "category": "food",
        "description": "Fresh food",
        "products": [{"name": "Bread", "price": 180, "currency": "INR"}],
        "hours": ["Mon-Sat 9-8"],
        "contact": {"whatsapp": "9876543210"},
        "location": {"city": "Mumbai"},
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize("category", ["food", "apparel", "electronics", "pharmacy", "services"])
def test_shop_name_script_is_escaped(category):
    html = render(category, spec(category=category, shop_name=PAYLOAD), get_palette(category))
    assert PAYLOAD not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize("category", ["food", "services"])
def test_description_attribute_payload_is_escaped(category):
    html = render(category, spec(category=category, description=ATTR_PAYLOAD), get_palette(category))

    # JSON-LD is a data block: the parser does not execute tags inside it, and
    # the separate terminator test proves `</script>` cannot break out.
    import json
    import re

    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert len(blocks) == 1
    json.loads(blocks[0])  # still valid JSON

    markup = html.replace(blocks[0], "")
    # Outside the data block the payload must not form a live tag or attribute.
    assert "<img src=x" not in markup
    assert 'onerror="alert(1)"' not in markup
    assert "&lt;img" in markup or "&#34;&gt;" in markup or "&quot;&gt;" in markup


def test_product_name_is_escaped():
    html = render(
        "food",
        spec(products=[{"name": "<b>x</b>", "price": 10, "currency": "INR"}]),
        get_palette("food"),
    )
    assert "<b>x</b>" not in html
    assert "&lt;b&gt;" in html


def test_fallback_template_is_escaped():
    # A missing template forces the fallback path.
    html = render("does-not-exist", spec(shop_name=PAYLOAD), get_palette("food"))
    assert PAYLOAD not in html
    assert "&lt;script&gt;" in html
