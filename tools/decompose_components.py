"""
decompose_components.py — Offline tool: converts scraped design-reference
sections into component_library entries (JSON files).

Reads:  data/design-reference/{category}/{site-slug}/sections.json
Writes: data/component-library/{section_type}/{category}-{site-slug}.json

Each entry follows component_library.schema.json:
  { category, section_type, html, css, source_url, review_status }

This is a research/offline tool, NOT part of the live pipeline.
Run after scrape_design_reference.py has collected reference data.

Usage:
    python tools/decompose_components.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
DESIGN_REF = DATA_ROOT / "design-reference"
COMPONENT_LIB = DATA_ROOT / "component-library"

SECTION_TYPES = ["nav", "hero", "product_grid", "contact"]


def decompose_site(category: str, site_dir: Path) -> list[dict]:
    sections_file = site_dir / "sections.json"
    if not sections_file.exists():
        return []

    sections = json.loads(sections_file.read_text(encoding="utf-8"))
    entries = []

    for section_type in SECTION_TYPES:
        if section_type not in sections:
            continue

        section = sections[section_type]
        html = section.get("html", "")
        css = section.get("computed_css", {})

        if not html:
            continue

        css_str = "; ".join(f"{k}: {v}" for k, v in css.items() if v)

        entry = {
            "category": category,
            "section_type": section_type,
            "html": html,
            "css": css_str,
            "source_url": None,
            "review_status": "PENDING",
            "reviewed_by": None,
        }
        entries.append(entry)

    return entries


def save_entry(entry: dict, site_slug: str) -> Path:
    section_type = entry["section_type"]
    category = entry["category"]
    out_dir = COMPONENT_LIB / section_type
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{category}-{site_slug}.json"
    out_path = out_dir / filename
    out_path.write_text(json.dumps(entry, indent=2), encoding="utf-8")
    return out_path


def main() -> None:
    if not DESIGN_REF.exists():
        print(f"No design-reference directory at {DESIGN_REF}")
        print("Run scrape_design_reference.py first.")
        return

    total = 0
    for category_dir in sorted(DESIGN_REF.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        category = category_dir.name

        for site_dir in sorted(category_dir.iterdir()):
            if not site_dir.is_dir():
                continue

            entries = decompose_site(category, site_dir)
            for entry in entries:
                path = save_entry(entry, site_dir.name)
                print(f"  [{entry['review_status']}] {path.relative_to(DATA_ROOT)}")
                total += 1

    print(f"\nDecomposed {total} component entries from design references.")


if __name__ == "__main__":
    main()
