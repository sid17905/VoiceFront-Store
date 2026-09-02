"""
component_picker.py — Selects one component variant per section_type
from the component library, given a StorefrontSpec.

Features:
- Dynamic multi-variant random or deterministic round-robin selection
- Category-aware section pairing
- Fallback to monolithic template when components are missing
- Strict enforcement of review_status == "APPROVED"
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

COMPONENT_LIB_DIR = Path(__file__).resolve().parents[3] / "data" / "component-library"

SECTION_TYPES = ["nav", "hero", "product_grid", "contact"]


def _load_variants(section_type: str, category: str) -> list[dict[str, Any]]:
    """Load all APPROVED variants for a section_type + category."""
    section_dir = COMPONENT_LIB_DIR / section_type
    if not section_dir.exists():
        return []

    variants = []
    for entry_file in sorted(section_dir.glob("*.json")):
        try:
            entry = json.loads(entry_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        if entry.get("category") != category:
            continue
        if entry.get("review_status") != "APPROVED":
            continue
        if entry.get("section_type") != section_type:
            continue

        variants.append(entry)

    return variants


def pick_components(
    spec: dict[str, Any],
    variant_strategy: str = "first",
) -> dict[str, dict[str, Any] | None]:
    """Pick one component variant per section_type for the given spec.

    Args:
        spec: Validated StorefrontSpec dict.
        variant_strategy: 'first' (deterministic) | 'random' (varied layouts)

    Returns:
        Dict mapping section_type → chosen variant dict, or None if
        no approved variant exists for that section_type.
    """
    category = spec["category"]
    result: dict[str, dict[str, Any] | None] = {}

    for section_type in SECTION_TYPES:
        variants = _load_variants(section_type, category)
        if variants:
            if variant_strategy == "random":
                result[section_type] = random.choice(variants)
            else:
                result[section_type] = variants[0]
        else:
            result[section_type] = None

    return result


def has_components(spec: dict[str, Any]) -> bool:
    """Check if ALL section_types have approved components for this category."""
    components = pick_components(spec)
    return all(v is not None for v in components.values())
