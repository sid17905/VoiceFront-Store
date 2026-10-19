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


def vary_palette(p: "Palette", seed: str) -> "Palette":
    """Deterministic per-shop hue shift (+/-30 deg) of the category palette."""
    import colorsys, hashlib
    if not seed:
        return p
    shift = ((int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % 121) - 60) / 360.0

    def rot(hexc: str) -> str:
        r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r, g, b = colorsys.hls_to_rgb((h + shift) % 1.0, l, s)
        return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))

    return Palette(primary=rot(p.primary), secondary=rot(p.secondary),
                   accent=rot(p.accent), text=p.text, background=p.background)


# Curated, on-theme variants per category: (primary, secondary, accent).
_VARIANTS = {
    "food": [("#935116", "#FCF3CF", "#D35400"), ("#6E2C00", "#FAE5D3", "#CA6F1E"),
             ("#922B21", "#FADBD8", "#E74C3C"), ("#7D6608", "#FCF3CF", "#D68910"),
             ("#A04000", "#FDEBD0", "#F39C12"), ("#78281F", "#F9EBEA", "#EC7063"),
             ("#5D4037", "#EFEBE9", "#FF8F00")],
    "apparel": [("#212F3C", "#FDEDEC", "#E74C3C"), ("#6E4B3A", "#F6EFE7", "#B9770E"),
                ("#4D5D3A", "#F1F5E9", "#A3A33A"), ("#512E5F", "#F4ECF7", "#D4AC0D"),
                ("#0E6655", "#E8F8F5", "#B7950B")],
    "electronics": [("#1B2631", "#EAECEE", "#17A589"), ("#4A148C", "#EDE7F6", "#7C4DFF"),
                    ("#0B5345", "#D1F2EB", "#16A085"), ("#154360", "#D6EAF8", "#F39C12"),
                    ("#B03A2E", "#FDEDEC", "#E67E22")],
    "pharmacy": [("#117A65", "#D1F2EB", "#1ABC9C"), ("#1F618D", "#D6EAF8", "#27AE60"),
                 ("#0E6251", "#E8F6F3", "#52BE80"), ("#2874A6", "#EBF5FB", "#48C9B0")],
    "services": [("#1B4F72", "#D4E6F1", "#2E86C1"), ("#0B5345", "#D1F2EB", "#17A589"),
                 ("#34495E", "#EAEDED", "#F39C12"), ("#6C3483", "#F4ECF7", "#AF7AC5"),
                 ("#7B241C", "#F9EBEA", "#CD6155")],
}


def vary_palette(p: "Palette", seed: str) -> "Palette":
    """Pick a curated on-theme variant (base palette included) from a stable hash of the shop name."""
    import hashlib
    if not seed:
        return p
    cat = next((k for k, v in CATEGORY_PALETTES.items() if v == p), None)
    options = [None] + _VARIANTS.get(cat, [])
    i = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % len(options)
    if options[i] is None:
        return p
    pr, se, ac = options[i]
    return Palette(primary=pr, secondary=se, accent=ac, text=p.text, background=p.background)
