"""
generate_visualizer.py — Generates the pipeline visualizer HTML page
from the actual component library data + provenance.

Output: docs/procedure/pipeline-visualizer.html

Usage:
    python tools/generate_visualizer.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
COMPONENT_LIB = DATA_ROOT / "component-library"
OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "procedure" / "pipeline-visualizer.html"
TEMPLATE = OUTPUT

SECTION_TYPES = ["nav", "hero", "product_grid", "contact"]


def load_components() -> dict[str, list[dict]]:
    components: dict[str, list[dict]] = {}
    for section_type in SECTION_TYPES:
        section_dir = COMPONENT_LIB / section_type
        if not section_dir.exists():
            continue
        for entry_file in sorted(section_dir.glob("*.json")):
            try:
                entry = json.loads(entry_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if entry.get("review_status") != "APPROVED":
                continue
            prov = entry.get("provenance", {})
            cat = entry.get("category", "unknown")
            flat = {
                "variant_id": entry.get("variant_id", "unknown"),
                "section_type": entry.get("section_type", "unknown"),
                "source_url": prov.get("source_url", entry.get("source_url", "")),
                "source_selector": prov.get("source_selector", "N/A"),
                "source_css_path": prov.get("source_css_path", "N/A"),
                "source_html_snippet": prov.get("source_html_snippet", "N/A"),
                "source_bounding_box": prov.get("source_bounding_box", {}),
                "adaptation_notes": prov.get("adaptation_notes", ""),
                "our_html": entry.get("html", ""),
                "our_css": entry.get("css", ""),
            }
            components.setdefault(cat, []).append(flat)
    return components


def generate():
    components = load_components()
    data_json = json.dumps(components, indent=2, ensure_ascii=False)

    html = TEMPLATE.read_text(encoding="utf-8")

    import re
    html = re.sub(
        r"const COMPONENTS = \{.*?\};\n",
        f"const COMPONENTS = {data_json};\n",
        html,
        flags=re.DOTALL,
    )

    TEMPLATE.write_text(html, encoding="utf-8")
    total = sum(len(v) for v in components.values())
    print(f"Pipeline visualizer updated: {TEMPLATE}")
    print(f"  {total} components across {len(components)} categories")


if __name__ == "__main__":
    generate()
