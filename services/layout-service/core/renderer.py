"""
renderer.py — Jinja2 server-side render.

Two rendering paths:
1. Component assembly: picks one variant per section_type from the
   component library, renders each via Jinja2, assembles into a page.
   Only used when ALL section_types have approved variants.
2. Monolithic fallback: renders the category's .jinja2 template directly.
   Used when components are incomplete or unavailable.

Security: autoescaping is ON. All conditional structure is resolved
before the template sees the context dict — Jinja2 never calls back
into Python logic (Architect.md L4 constraint).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from core.palette_engine import Palette

_TEMPLATE_DIR = Path(os.environ.get(
    "LAYOUT_TEMPLATE_DIR",
    Path(__file__).resolve().parents[1] / "templates",
))

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
    trim_blocks=True,
    lstrip_blocks=True,
)

_PAGE_SHELL = """\
<!DOCTYPE html>
<html lang="hi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{shop_name}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: {text}; background: {background}; line-height: 1.6; }}
    a, button {{ min-width: 24px; min-height: 24px; display: inline-flex; align-items: center; justify-content: center; }}
    img {{ max-width: 100%; height: auto; display: block; }}
    .nav {{ background: {primary}; color: #fff; padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; }}
    .nav h1 {{ font-size: 1.2rem; font-weight: 700; }}
    .nav-links {{ display: flex; gap: 16px; }}
    .nav-links a {{ color: #fff; text-decoration: none; font-size: 0.85rem; }}
    .nav-links a:focus-visible {{ outline: 2px solid #fff; outline-offset: 2px; border-radius: 2px; }}
    .hero {{ background: {secondary}; padding: 32px 24px; text-align: center; }}
    .hero h2 {{ font-size: 1.4rem; margin-bottom: 8px; color: {primary}; }}
    .hero p {{ max-width: 600px; margin: 0 auto; }}
    .products {{ padding: 24px 16px; max-width: 1000px; margin: 0 auto; }}
    .products h2 {{ font-size: 1.2rem; margin-bottom: 16px; color: {primary}; }}
    .product-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }}
    .product-card {{ border: 1px solid #e0e0e0; border-radius: 8px; padding: 16px; background: #fff; }}
    .product-card h3 {{ font-size: 1rem; margin-bottom: 4px; }}
    .product-card .price {{ font-size: 1.1rem; font-weight: 700; color: {accent}; }}
    .product-card .desc {{ font-size: 0.85rem; color: #666; margin-top: 4px; }}
    .hours {{ padding: 24px 16px; max-width: 600px; margin: 0 auto; }}
    .hours h2 {{ font-size: 1.2rem; margin-bottom: 12px; color: {primary}; }}
    .hours ul {{ list-style: none; }}
    .hours li {{ padding: 6px 0; border-bottom: 1px solid #eee; font-size: 0.9rem; }}
    .contact {{ padding: 24px 16px; max-width: 600px; margin: 0 auto; }}
    .contact h2 {{ font-size: 1.2rem; margin-bottom: 12px; color: {primary}; }}
    .contact-links {{ display: flex; flex-wrap: wrap; gap: 12px; }}
    .whatsapp-btn {{ background: #25D366; color: #fff; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: 600; }}
    .whatsapp-btn:hover {{ background: #1da851; }}
    .phone-link {{ color: {primary}; text-decoration: underline; padding: 10px 0; }}
    footer {{ text-align: center; padding: 24px 16px; font-size: 0.8rem; color: #999; border-top: 1px solid #eee; margin-top: 32px; }}
    @media (max-width: 480px) {{
      .product-grid {{ grid-template-columns: 1fr; }}
      .nav {{ flex-direction: column; gap: 8px; text-align: center; }}
    }}
  </style>
  {json_ld}
</head>
<body>
  {nav_html}
  {hero_html}
  {products_html}
  {hours_html}
  {contact_html}
  <footer><p>{shop_name} &mdash; Powered by VoiceFront</p></footer>
</body>
</html>"""


def _build_context(spec: dict[str, Any], palette: Palette) -> dict[str, Any]:
    return {
        "shop_name": spec["shop_name"],
        "category": spec["category"],
        "description": spec.get("description", ""),
        "products": spec.get("products", []),
        "hours": spec.get("hours", []),
        "location": spec.get("location"),
        "contact": spec.get("contact", {}),
        "colors": {
            "primary": palette.primary,
            "secondary": palette.secondary,
            "accent": palette.accent,
            "text": palette.text,
            "background": palette.background,
        },
    }


def _render_json_ld(spec: dict[str, Any]) -> str:
    schema_type = {
        "food": "FoodEstablishment",
        "apparel": "ClothingStore",
        "electronics": "ElectronicsStore",
        "pharmacy": "PharmacyOrDrugstore",
        "services": "LocalBusiness",
    }.get(spec["category"], "LocalBusiness")

    parts = [
        '<script type="application/ld+json">',
        '{"@context":"https://schema.org","@type":"' + schema_type + '",',
        '"name":"' + spec["shop_name"] + '"',
    ]
    if spec.get("description"):
        parts.append(',"description":"' + spec["description"] + '"')
    if spec.get("contact", {}).get("whatsapp"):
        parts.append(',"url":"https://wa.me/' + spec["contact"]["whatsapp"] + '"')
    parts.append("}</script>")
    return "\n".join(parts)


def _render_section(
    section_html: str,
    section_css: str,
    context: dict[str, Any],
) -> str:
    """Render a component section's HTML template with the given context."""
    tmpl = _env.from_string(section_html)
    rendered = tmpl.render(**context)
    if section_css:
        style_tag = f"<style>{rendered}\n{{{{ block('extra_css') }}}}</style>"
        css_tmpl = _env.from_string(f"<style>{section_css}</style>")
        css_rendered = css_tmpl.render(**context)
        return f"{rendered}\n{css_rendered}"
    return rendered


def render_components(
    spec: dict[str, Any],
    palette: Palette,
    components: dict[str, dict[str, Any] | None],
) -> str:
    """Assemble a page from individual component variants.

    Each component's HTML and CSS are rendered separately via Jinja2,
    then assembled into a complete HTML document.

    Args:
        spec: Validated StorefrontSpec dict.
        palette: Colour palette from palette_engine.
        components: Dict mapping section_type → variant dict (or None).

    Returns:
        Complete HTML document string.
    """
    ctx = _build_context(spec, palette)
    json_ld = _render_json_ld(spec)

    nav_html = ""
    hero_html = ""
    products_html = ""
    hours_html = ""
    contact_html = ""

    for section_type, variant in components.items():
        if variant is None:
            continue

        rendered = _render_section(variant["html"], variant.get("css", ""), ctx)

        if section_type == "nav":
            nav_html = rendered
        elif section_type == "hero":
            hero_html = rendered
        elif section_type == "product_grid":
            products_html = rendered
        elif section_type == "contact":
            contact_html = rendered

    hours_parts = []
    if spec.get("hours"):
        hours_parts.append('<section class="hours" id="hours" aria-label="Opening hours">')
        hours_parts.append("<h2>Hours</h2><ul>")
        for h in spec["hours"]:
            hours_parts.append(f"<li>{h}</li>")
        hours_parts.append("</ul></section>")
    hours_html = "\n".join(hours_parts)

    return _PAGE_SHELL.format(
        shop_name=spec["shop_name"],
        primary=palette.primary,
        secondary=palette.secondary,
        accent=palette.accent,
        text=palette.text,
        background=palette.background,
        json_ld=json_ld,
        nav_html=nav_html,
        hero_html=hero_html,
        products_html=products_html,
        hours_html=hours_html,
        contact_html=contact_html,
    )


def render(
    template_id: str,
    spec: dict[str, Any],
    palette: Palette,
) -> str:
    """Render a StorefrontSpec into an HTML string.

    Tries component assembly first (all section_types must have
    approved variants). Falls back to monolithic template if not.

    Args:
        template_id: One of food|apparel|electronics|pharmacy|services.
        spec: Validated StorefrontSpec dict.
        palette: Colour palette from palette_engine.

    Returns:
        Complete HTML document as a string.
    """
    from core.component_picker import pick_components, has_components

    if has_components(spec):
        components = pick_components(spec)
        return render_components(spec, palette, components)

    template = _env.get_template(f"{template_id}.jinja2")
    context = _build_context(spec, palette)
    return template.render(**context)
