"""
tools/scrape_design_reference.py — Phase A (design-reference scraper)

Offline research tool, NOT part of the live pipeline. Playwright visits a
curated list of public retail sites, captures rendered HTML + computed CSS
for a few key sections, and saves them locally for Person C to look at while
hand-building the 5 MVP Jinja2 templates (Architect.md L4).

Nothing scraped here is ever served to a real user. This intentionally stays
inside the MVP's "classification, not generation" boundary.

Usage:
    python tools/scrape_design_reference.py sites.json

sites.json format:
[
  {"category": "food", "url": "https://example-restaurant-site.com"},
  {"category": "apparel", "url": "https://example-clothing-site.com"}
]

Output: data/design-reference/{category}/{site-slug}/
    page.html          — full rendered HTML
    sections.json       — {section_name: {html, computed_css}} for nav/hero/product-grid/contact
    screenshot.png      — full-page screenshot for quick visual scanning
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "data" / "design-reference"

# CSS selectors we try, in order, for each section of interest. Best-effort —
# real sites vary wildly, this is a research aid, not a guaranteed extractor.
SECTION_SELECTORS = {
    "nav": ["nav", "header", "[role=navigation]"],
    "hero": [".hero", "[class*=hero]", "header + section", "main > section:first-of-type"],
    "product_grid": [
        "[class*=product-grid]", "[class*=products]", "[class*=menu]", "main ul", "main .grid",
    ],
    "contact": ["footer", "[class*=contact]", "[id*=contact]"],
}

# Only the CSS properties actually useful for adapting a look-and-feel —
# capturing all ~300 computed properties per element is noise, not signal.
RELEVANT_CSS_PROPS = [
    "color", "background-color", "font-family", "font-size", "font-weight",
    "padding", "margin", "border-radius", "box-shadow", "display", "grid-template-columns",
]


def _slug(url: str) -> str:
    host = urlparse(url).netloc
    return re.sub(r"[^a-z0-9-]+", "-", host.lower()).strip("-")


def _computed_css(page, selector: str) -> dict | None:
    return page.evaluate(
        """([sel, props]) => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const style = window.getComputedStyle(el);
            const out = {};
            for (const p of props) out[p] = style.getPropertyValue(p);
            return out;
        }""",
        [selector, RELEVANT_CSS_PROPS],
    )


def _first_matching_selector(page, candidates: list[str]) -> str | None:
    for sel in candidates:
        if page.evaluate("(sel) => !!document.querySelector(sel)", sel):
            return sel
    return None


def scrape_site(page, category: str, url: str) -> None:
    site_dir = OUTPUT_ROOT / category / _slug(url)
    site_dir.mkdir(parents=True, exist_ok=True)

    page.goto(url, wait_until="load", timeout=30_000)

    (site_dir / "page.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(site_dir / "screenshot.png"), full_page=True)

    sections = {}
    for name, candidates in SECTION_SELECTORS.items():
        sel = _first_matching_selector(page, candidates)
        if not sel:
            continue
        html = page.evaluate("(sel) => document.querySelector(sel)?.outerHTML || null", sel)
        css = _computed_css(page, sel)
        sections[name] = {"matched_selector": sel, "html": html, "computed_css": css}

    (site_dir / "sections.json").write_text(json.dumps(sections, indent=2), encoding="utf-8")
    print(f"[ok] {category}/{_slug(url)} -> {len(sections)} sections captured")


def main(sites_file: str) -> None:
    sites = json.loads(Path(sites_file).read_text(encoding="utf-8"))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        for entry in sites:
            try:
                scrape_site(page, entry["category"], entry["url"])
            except Exception as exc:  # one bad site shouldn't kill the whole run
                print(f"[skip] {entry['url']}: {exc}")
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scrape_design_reference.py sites.json")
        raise SystemExit(1)
    main(sys.argv[1])
