"""
provenance_viewer.py — Opens the original reference site in Playwright
and highlights the exact element that a component was derived from.

Saves a screenshot with the element highlighted + annotated, so you can
show professors exactly which part of the original site inspired each
component.

Usage:
    python tools/provenance_viewer.py <component_json_path>

Example:
    python tools/provenance_viewer.py data/component-library/nav/food-classic.json

Output: data/provenance-highlights/{variant_id}.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
HIGHLIGHTS_DIR = DATA_ROOT / "provenance-highlights"


def highlight_element(component_path: str) -> str | None:
    """Open the source site and highlight the referenced element.

    Returns the path to the saved screenshot, or None on failure.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright not installed. Run: pip install playwright && playwright install")
        return None

    entry = json.loads(Path(component_path).read_text(encoding="utf-8"))
    prov = entry.get("provenance", {})

    source_url = prov.get("source_url", entry.get("source_url"))
    selector = prov.get("source_selector")
    variant_id = entry.get("variant_id", "unknown")

    if not source_url or not selector:
        print(f"Error: component missing source_url or source_selector in provenance")
        return None

    print(f"Opening {source_url} ...")
    print(f"Highlighting element: {selector}")

    HIGHLIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = HIGHLIGHTS_DIR / f"{variant_id}.png"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        try:
            page.goto(source_url, wait_until="load", timeout=30000)
        except Exception as exc:
            print(f"Error loading {source_url}: {exc}")
            browser.close()
            return None

        # Inject highlight overlay via JS
        highlight_js = """(sel) => {
            const el = document.querySelector(sel);
            if (!el) return false;

            // Scroll element into view
            el.scrollIntoView({ behavior: 'instant', block: 'center' });

            // Add red border + semi-transparent overlay
            el.style.outline = '4px solid #ff0000';
            el.style.outlineOffset = '2px';
            el.style.position = 'relative';

            // Add label
            const label = document.createElement('div');
            label.textContent = '>>> DERIVED COMPONENT <<<' + ' | Selector: ' + sel;
            label.style.cssText = 'position:absolute;top:-28px;left:0;background:#ff0000;color:#fff;padding:4px 8px;font-size:12px;font-family:monospace;z-index:99999;white-space:nowrap;border-radius:2px;';
            el.appendChild(label);

            // Dim everything else
            const overlay = document.createElement('div');
            overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.3);pointer-events:none;z-index:99998;';
            document.body.appendChild(overlay);

            return true;
        }"""

        found = page.evaluate(highlight_js, selector)
        if not found:
            print(f"Warning: selector '{selector}' not found on page, taking screenshot anyway")

        # Wait a moment for scroll to settle
        page.wait_for_timeout(500)

        page.screenshot(path=str(output_path))
        print(f"Screenshot saved: {output_path}")

        browser.close()

    return str(output_path)


def main():
    if len(sys.argv) != 2:
        print("Usage: python provenance_viewer.py <component_json_path>")
        print("Example: python provenance_viewer.py data/component-library/nav/food-classic.json")
        sys.exit(1)

    component_path = sys.argv[1]
    if not Path(component_path).exists():
        print(f"Error: file not found: {component_path}")
        sys.exit(1)

    result = highlight_element(component_path)
    if result:
        print(f"\nDone! Open the screenshot to see the highlighted element.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
