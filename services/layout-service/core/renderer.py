"""
services/layout-service/core/renderer.py

Jinja2 server-side render.

Security notes (audit S1/S2/S5/S6/S7):
- autoescape is ON for every template, including .jinja2.
- JSON-LD is serialised in Python and its `</` sequences are escaped so a
  description cannot terminate the <script> block.
- The fallback page is a real template (_fallback.jinja2), not a str.format
  shell — the old shell contained unescaped JS braces and always raised.
- No invented contact data or dead asset paths are emitted.

All conditional structure is resolved before the template sees the context
(Architect.md L4): templates never call back into Python.
"""

from __future__ import annotations

import logging
import os
import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from core.palette_engine import Palette, vary_palette

logger = logging.getLogger(__name__)

_configured_dir = os.environ.get("LAYOUT_TEMPLATE_DIR", "").strip()
_TEMPLATE_DIR = (
    Path(_configured_dir) if _configured_dir
    else Path(__file__).resolve().parents[1] / "templates"
)

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def _resolve_image_url(product_name: str, category: str) -> str:
    """Return a local asset path for the product image.

    All assets live under ``/assets/<category>/`` and are chosen by the
    most specific keyword match.  If nothing is found a generic
    branded‑gradient placeholder is returned.
    """
    name_lower = product_name.lower()

    # Category‑specific keyword → asset
    assets: dict[str, dict[str, str]] = {
        "services": {
            "gym": "assets/services/dumbbell.svg",
            "fitness": "assets/services/dumbbell.svg",
            "workout": "assets/services/dumbbell.svg",
            "training": "assets/services/dumbbell.svg",
            "iron": "assets/services/dumbbell.svg",
        },
        "food": {
            "coffee": "assets/food/coffee.svg",
            "cafe": "assets/food/coffee.svg",
            "espresso": "assets/food/coffee.svg",
            "tea": "assets/food/tea.svg",
        },
        "electronics": {
            "phone": "assets/electronics/phone.svg",
            "laptop": "assets/electronics/laptop.svg",
            "gadget": "assets/electronics/gadget.svg",
        },
        "apparel": {
            "shirt": "assets/apparel/shirt.svg",
            "dress": "assets/apparel/dress.svg",
            "saree": "assets/apparel/saree.svg",
        },
        "pharmacy": {
            "medicine": "assets/pharmacy/medicine.svg",
            "drug": "assets/pharmacy/drug.svg",
            "healthcare": "assets/pharmacy/healthcare.svg",
        },
    }

    # Find a keyword that belongs to the current category.
    chosen = None
    if category in assets:
        for kw, path in assets[category].items():
            if kw in name_lower:
                chosen = path
                break

    if chosen:
        return chosen

    # No keyword matched – return a branded gradient placeholder.
    return f"assets/{category}/placeholder.svg"



def _price_display(value: Any, currency: str = "INR") -> str:
    """Format a price without ever raising.

    `ProductItem.price` is `float | str | None`; the templates previously did
    `"%.0f" | format(product.price)`, which raises on None and on string prices.
    """
    if value is None or value == "":
        return "Ask for price"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        symbol = {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}.get(currency, f"{currency} ")
        return f"{symbol}{value:,.0f}"
    return str(value)


def _location_display(location: dict[str, Any] | None) -> str:
    """Join the address fields that actually exist on LocationInfo.

    The templates used to read `location.raw_text`, a field removed from the
    schema, so address output was always blank.
    """
    if not isinstance(location, dict):
        return ""
    parts = [
        location.get("address"),
        location.get("city"),
        location.get("state"),
        location.get("pincode"),
    ]
    return ", ".join(str(p).strip() for p in parts if p and str(p).strip())


def _placeholder_svg(label: str, color: str = "#64748b") -> str:
    """Deterministic inline placeholder — no missing asset paths, no network."""
    from urllib.parse import quote
    from html import escape as _escape

    text = _escape((label or "Item")[:14])
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144">'
        f'<rect width="100%" height="100%" fill="{color}"/>'
        f'<text x="50%" y="52%" text-anchor="middle" fill="#ffffff" '
        f'font-family="sans-serif" font-size="14">{text}</text></svg>'
    )
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def _build_context(spec: dict[str, Any], palette: Palette) -> dict[str, Any]:
    category = spec.get("category", "services")

    # Local, self-contained hero image. No third-party request from a
    # customer-facing page, and nothing to 404.
    hero_image = _placeholder_svg(spec.get("shop_name", "Store"), palette.primary)

    products = []
    for p in (spec.get("products") or _suggested_products(category)):
        p_copy = dict(p)
        p_copy["price_display"] = _price_display(p.get("price"), p.get("currency", "INR"))
        p_copy["thumbnail"] = (
            p.get("image_url")
            or _icon_svg(p.get("name", "Item"), palette.secondary, category)
        )
        products.append(p_copy)

    contact = spec.get("contact") or {}
    whatsapp = str(contact.get("whatsapp") or "").strip()

    return {
        "shop_name": spec["shop_name"],
        "category": category,
        "description": spec.get("description", ""),
        "products": products,
        "hours": spec.get("hours", []),
        "location": spec.get("location"),
        "location_display": _location_display(spec.get("location")),
        "contact": contact,
        "whatsapp_number": whatsapp,
        "hero_image": hero_image,
        "json_ld": _render_json_ld(spec),
        "primary": palette.primary,
        "secondary": palette.secondary,
        "accent": palette.accent,
        "text": palette.text,
        "background": palette.background,
    }


def _render_json_ld(spec: dict[str, Any]) -> Markup:
    """Serialise JSON-LD safely for inline use in a <script> block."""
    schema_type = {
        "food": "FoodEstablishment",
        "apparel": "ClothingStore",
        "electronics": "ElectronicsStore",
        "pharmacy": "PharmacyOrDrugstore",
        "services": "LocalBusiness",
    }.get(spec.get("category", "services"), "LocalBusiness")

    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": spec.get("shop_name", ""),
    }
    if spec.get("description"):
        data["description"] = spec["description"]
    if spec.get("products"):
        data["hasOfferCatalog"] = {
            "@type": "OfferCatalog",
            "name": "Products",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {"@type": "Product", "name": p.get("name", "")},
                    "price": p.get("price"),
                    "priceCurrency": p.get("currency", "INR"),
                }
                for p in spec["products"][:50]
                if isinstance(p, dict)
            ],
        }
    if spec.get("hours"):
        data["openingHours"] = list(spec["hours"])
    address = _location_display(spec.get("location"))
    if address:
        data["address"] = {"@type": "PostalAddress", "streetAddress": address}
    contact = spec.get("contact") or {}
    if contact.get("whatsapp"):
        data["url"] = f"https://wa.me/{contact['whatsapp']}"
    if contact.get("phone"):
        data["telephone"] = str(contact["phone"])

    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return Markup(f'<script type="application/ld+json">{payload}</script>')


def render(
    template_id: str,
    spec: dict[str, Any],
    palette: Palette,
) -> str:
    """Render a category template, falling back to the generic shell.

    Only template-level failures trigger the fallback. Data errors are allowed
    to raise so callers see a real 500 instead of a silently degraded page.
    """
    from jinja2 import TemplateError

    palette = vary_palette(palette, str(spec.get('shop_name', '')))
    ctx = _build_context(spec, palette)
    template_ctx = {
        "shop_name": ctx["shop_name"],
        "category": ctx["category"],
        "description": ctx["description"],
        "products": ctx["products"],
        "hours": ctx["hours"],
        "location": ctx["location"],
        "location_display": ctx["location_display"],
        "contact": ctx["contact"],
        "whatsapp_number": ctx["whatsapp_number"],
        "hero_image": ctx["hero_image"],
        "json_ld": ctx["json_ld"],
        "colors": {
            "primary": palette.primary,
            "secondary": palette.secondary,
            "accent": palette.accent,
            "text": palette.text,
            "background": palette.background,
        },
    }

    try:
        template = _env.get_template(f"{template_id}.jinja2")
        return template.render(**template_ctx)
    except TemplateError as exc:
        logger.warning(
            "template %r unavailable (%s); using fallback",
            template_id, type(exc).__name__,
            extra={"template_id": template_id},
        )
        fallback = _env.get_template("_fallback.jinja2")
        return fallback.render(**template_ctx)


def render_components(
    spec: dict[str, Any],
    palette: Palette,
    components: dict[str, dict[str, Any] | None],
) -> str:
    """Assemble an approved component variant per section type.

    Falls back to the monolithic category template when any section is
    missing. Invariant: passing `components` must change the output.
    """
    if not components or any(v is None for v in components.values()):
        return render(spec.get("category", "services"), spec, palette)

    palette = vary_palette(palette, str(spec.get('shop_name', '')))
    ctx = _build_context(spec, palette)
    ctx["colors"] = {
        "primary": palette.primary,
        "secondary": palette.secondary,
        "accent": palette.accent,
        "text": palette.text,
        "background": palette.background,
    }

    from jinja2 import BaseLoader
    from jinja2.sandbox import SandboxedEnvironment

    sandbox = SandboxedEnvironment(loader=BaseLoader(), autoescape=True)
    sections: list[str] = []
    for section in ("nav", "hero", "product_grid", "contact"):
        variant = components[section]
        body = sandbox.from_string(variant.get("html", "")).render(**ctx)
        css = sandbox.from_string(variant.get("css", "")).render(**ctx)
        sections.append(f"<style>{css}</style>{body}" if css else body)

    page = (
        "<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{ctx['shop_name']}</title>{ctx['json_ld']}</head><body>"
        + "".join(sections)
        + "</body></html>"
    )
    return page


def _icon_svg(label: str, color: str, category: str) -> str:
    """Deterministic inline illustration: gradient tile plus a keyword-matched emoji."""
    from urllib.parse import quote
    n = (label or "").lower()
    icons = [
        ("cake", "\U0001F370"), ("cookie", "\U0001F36A"), ("bread", "\U0001F35E"), ("pizza", "\U0001F355"),
        ("burger", "\U0001F354"), ("biryani", "\U0001F35B"), ("rice", "\U0001F35B"), ("coffee", "\u2615"),
        ("tea", "\U0001F375"), ("sweet", "\U0001F36C"), ("ice", "\U0001F366"), ("juice", "\U0001F9C3"),
        ("shirt", "\U0001F455"), ("jean", "\U0001F456"), ("dress", "\U0001F457"), ("saree", "\U0001F97B"),
        ("shoe", "\U0001F45F"), ("jacket", "\U0001F9E5"), ("phone", "\U0001F4F1"), ("screen", "\U0001F4F1"),
        ("laptop", "\U0001F4BB"), ("battery", "\U0001F50B"), ("charger", "\U0001F50C"), ("tv", "\U0001F4FA"),
        ("headphone", "\U0001F3A7"), ("repair", "\U0001F527"), ("syrup", "\U0001F9F4"), ("tablet", "\U0001F48A"),
        ("paracetamol", "\U0001F48A"), ("medicine", "\U0001F48A"), ("gym", "\U0001F3CB"), ("haircut", "\u2702"),
    ]
    defaults = {"food": "\U0001F37D", "apparel": "\U0001F455", "electronics": "\U0001F50C",
                "pharmacy": "\U0001F48A", "services": "\U0001F6E0"}
    emoji = next((e for k, e in icons if k in n), defaults.get(category, "\U0001F6CD"))
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="160">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{color}"/><stop offset="1" stop-color="{color}" stop-opacity="0.55"/>'
        '</linearGradient></defs><rect width="100%" height="100%" fill="url(#g)"/>'
        f'<text x="50%" y="62%" text-anchor="middle" font-size="72">{emoji}</text></svg>'
    )
    return "data:image/svg+xml;charset=utf-8," + quote(svg)


def _suggested_products(category: str) -> list:
    """Generic, price-less sample items so an empty product list never renders an empty page."""
    names = {
        "food": ["Cake", "Cookies", "Bread", "Coffee"],
        "apparel": ["Shirt", "Jeans", "Dress", "Jacket"],
        "electronics": ["Phone", "Laptop", "Charger", "Headphones"],
        "pharmacy": ["Medicine", "Syrup", "Vitamins", "First Aid Kit"],
        "services": ["Consultation", "Repair Service", "Installation", "Maintenance"],
    }.get(category, ["Item 1", "Item 2", "Item 3"])
    return [{"name": n, "price": None, "description": "Sample item - replace with your own",
             "is_suggested": True} for n in names]
