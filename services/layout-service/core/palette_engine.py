"""
palette_engine.py — Category-to-colour-palette mapping.

Grounded in Labrecque & Milne (2012) colour-psychology associations:
  - food:       warm reds/oranges (appetite stimulation)
  - apparel:    neutral/earthy tones (elegance, trust)
  - electronics: cool blues (technology, reliability)
  - pharmacy:   clean greens (health, safety)
  - services:   professional indigo (competence, calm)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    primary: str
    secondary: str
    accent: str
    text: str
    background: str


CATEGORY_PALETTES: dict[str, Palette] = {
    "food": Palette(
        primary="#C0392B",
        secondary="#FDEBD0",
        accent="#E67E22",
        text="#2C3E50",
        background="#FDFEFE",
    ),
    "apparel": Palette(
        primary="#2C3E50",
        secondary="#F2F3F4",
        accent="#B7950B",
        text="#1C2833",
        background="#FAFAFA",
    ),
    "electronics": Palette(
        primary="#1A5276",
        secondary="#D6EAF8",
        accent="#2E86C1",
        text="#1B2631",
        background="#F8F9FA",
    ),
    "pharmacy": Palette(
        primary="#1E8449",
        secondary="#D5F5E3",
        accent="#27AE60",
        text="#1C2833",
        background="#FAFEFE",
    ),
    "services": Palette(
        primary="#4A235A",
        secondary="#E8DAEF",
        accent="#8E44AD",
        text="#1C2833",
        background="#FDFEFE",
    ),
}


def get_palette(category: str) -> Palette:
    """Return the colour palette for a given category.

    Raises ValueError for unknown categories — the template_classifier
    guarantees a valid category before this is called.
    """
    try:
        return CATEGORY_PALETTES[category]
    except KeyError:
        raise ValueError(
            f"Unknown category '{category}'. "
            f"Valid categories: {', '.join(sorted(CATEGORY_PALETTES))}"
        )
