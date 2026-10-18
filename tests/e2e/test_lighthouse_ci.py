"""Lighthouse / Core Web Vitals evaluation.

The previous version of this file asserted hardcoded mock scores (95/92/100/90).
A test that cannot fail is not evidence, so this file now does two honest
things:

1. `test_generated_page_seo_basics` runs on every CI push and checks the
   structural signals Lighthouse would score: title, meta description,
   viewport, language, a single <h1>, and image alt text.
2. `test_lighthouse_cli` runs the real Lighthouse CLI only when it is
   installed and `LIGHTHOUSE=1` is set. Otherwise it skips and says why. Its
   scores are printed, and the thresholds are set from the first real run —
   never invented (invariant I-T3).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _render_services_page() -> str:
    layout = ROOT / "services" / "layout-service"
    if str(layout) not in sys.path:
        sys.path.insert(0, str(layout))
    if "core" in sys.modules:
        del sys.modules["core"]
    from core.palette_engine import get_palette
    from core.renderer import render

    spec = {
        "shop_name": "Lighthouse Test Shop",
        "category": "services",
        "description": "A test storefront for structural checks.",
        "products": [{"name": "Consultation", "price": 500, "currency": "INR"}],
        "hours": ["Mon-Sat 9-6"],
        "contact": {"whatsapp": "9876543210"},
        "location": {"city": "Mumbai"},
    }
    return render("services", spec, get_palette("services"))


def test_generated_page_seo_basics():
    html = _render_services_page()

    assert "<title>" in html
    assert 'name="description"' in html
    assert "viewport" in html
    assert 'lang="en"' in html
    assert html.count("<h1") == 1
    assert html.count("<main") == 1
    assert "<img" not in html or 'alt="' in html


@pytest.mark.skipif(not os.getenv("LIGHTHOUSE"),
                    reason="set LIGHTHOUSE=1 with the lighthouse CLI installed")
def test_lighthouse_cli():
    binary = shutil.which("lighthouse")
    if binary is None:
        pytest.skip("lighthouse CLI not installed")

    html = _render_services_page()
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "index.html"
        page.write_text(html, encoding="utf-8")
        out = Path(tmp) / "report.json"
        subprocess.run(
            [binary, page.as_uri(), "--output=json",
             f"--output-path={out}", "--chrome-flags=--headless --no-sandbox",
             "--only-categories=performance,accessibility,best-practices,seo"],
            check=True, capture_output=True, timeout=180,
        )
        report = json.loads(out.read_text(encoding="utf-8"))

    scores = {k: report["categories"][k]["score"] * 100
              for k in ("performance", "accessibility", "best-practices", "seo")}
    print("Lighthouse scores:", scores)

    assert scores["accessibility"] >= 90
    assert scores["seo"] >= 90
