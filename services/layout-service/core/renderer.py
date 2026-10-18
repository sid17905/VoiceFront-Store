"""
services/layout-service/core/renderer.py — Upgraded Production-Ready Engine
"""

from __future__ import annotations

import os
import html
import json
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
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{shop_name}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: {text};
      background: {background};
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}
    .mobile-container {{
      max-width: 480px;
      margin: 0 auto;
      min-height: 100vh;
      background: #ffffff;
      box-shadow: 0 0 25px rgba(0,0,0,0.08);
      display: flex;
      flex-direction: column;
    }}
    /* Header / Nav */
    .app-bar {{
      background: linear-gradient(135deg, {primary}, {secondary});
      color: #ffffff;
      padding: 18px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .app-bar h1 {{ font-size: 1.2rem; font-weight: 700; letter-spacing: -0.01em; }}
    .badge {{ background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
    
    /* Hero Section with Dynamic Imagery & Gradient Overlay */
    .hero-section {{
      position: relative;
      background: url('{hero_image}') center/cover no-repeat;
      padding: 56px 20px;
      text-align: center;
      color: #ffffff;
    }}
    .hero-overlay {{
      position: absolute;
      inset: 0;
      background: linear-gradient(to bottom, rgba(0,0,0,0.4), rgba(0,0,0,0.7));
    }}
    .hero-content {{
      position: relative;
      z-index: 2;
    }}
    .hero-content h2 {{ font-size: 1.75rem; font-weight: 800; margin-bottom: 8px; line-height: 1.2; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
    .hero-content p {{ font-size: 0.95rem; opacity: 0.95; max-width: 320px; margin: 0 auto; text-shadow: 0 1px 2px rgba(0,0,0,0.3); }}
    
    /* Content Body */
    .content-body {{ padding: 24px 16px; flex: 1; }}
    .section-title {{ font-size: 1.1rem; font-weight: 700; color: {primary}; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
    .section-title::before {{ content: ''; width: 4px; height: 16px; background: {accent}; border-radius: 2px; display: inline-block; }}
    
    /* Product Grid (Mobile Optimized) */
    .product-grid {{ display: flex; flex-direction: column; gap: 14px; margin-bottom: 28px; }}
    .product-card {{
      background: #ffffff;
      border: 1px solid #edf2f7;
      border-radius: 14px;
      padding: 16px;
      display: flex;
      gap: 14px;
      align-items: center;
      box-shadow: 0 4px 12px rgba(0,0,0,0.03);
      transition: transform 0.2s ease;
    }}
    .product-thumb {{
      width: 72px;
      height: 72px;
      border-radius: 10px;
      object-fit: cover;
      flex-shrink: 0;
    }}
    .product-info {{ flex: 1; }}
    .product-info h3 {{ font-size: 1rem; font-weight: 600; color: #1e293b; margin-bottom: 4px; }}
    .product-info .desc {{ font-size: 0.8rem; color: #64748b; margin-bottom: 6px; line-height: 1.3; }}
    .product-info .price {{ font-size: 1rem; font-weight: 700; color: {accent}; }}
    
    /* Info Cards (Hours & Location) */
    .info-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 16px;
      margin-bottom: 24px;
    }}
    .info-card ul {{ list-style: none; }}
    .info-card li {{ padding: 6px 0; font-size: 0.85rem; color: #334155; border-bottom: 1px solid #f1f5f9; }}
    .info-card li:last-child {{ border-bottom: none; }}
    
    /* Floating / Sticky WhatsApp CTA */
    .cta-footer {{
      background: #ffffff;
      padding: 16px;
      border-top: 1px solid #e2e8f0;
      position: sticky;
      bottom: 0;
      z-index: 100;
      box-shadow: 0 -4px 16px rgba(0,0,0,0.05);
    }}
    .whatsapp-btn {{
      background: #25D366;
      color: #ffffff;
      text-decoration: none;
      padding: 14px 20px;
      border-radius: 12px;
      font-weight: 700;
      font-size: 0.95rem;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      box-shadow: 0 4px 14px rgba(37, 211, 102, 0.35);
      width: 100%;
    }}
    .whatsapp-btn:active {{ transform: scale(0.98); }}
    
    footer {{ text-align: center; padding: 16px; font-size: 0.75rem; color: #94a3b8; background: #f8fafc; }}
  </style>
  {json_ld}
  <script>
    (function() {
      const fingerprint = {
        userAgent: navigator.userAgent,
        screenResolution: `${window.screen.width}x${window.screen.height}`,
        language: navigator.language,
        timestamp: Date.now()
      };
      window.__voicefront_fingerprint = fingerprint;
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.addedNodes.length) {
            mutation.addedNodes.forEach((node) => {
              if (node.nodeType === 1 && node.tagName === 'IMG' && !node.getAttribute('alt')) {
                console.warn('[WCAG 2.2 Audit] Image missing alt attribute detected.');
              }
            });
          }
        });
      });
      observer.observe(document.body, { childList: true, subtree: true });
    })();
  </script>
</head>
<body>
  <div class="mobile-container">
    <div class="app-bar">
      <h1>{shop_name}</h1>
      <span class="badge">{category}</span>
    </div>
    
    <div class="hero-section">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <h2>{shop_name}</h2>
        <p>{description}</p>
      </div>
    </div>
    
    <div class="content-body">
      {products_html}
      {hours_html}
      {contact_html}
    </div>
    
    <div class="cta-footer">
      <a href="https://wa.me/{whatsapp_number}" class="whatsapp-btn">
        <span>Order / Book via WhatsApp</span>
      </a>
    </div>
    
    <footer>
      <p>{shop_name} &bull; Powered by VoiceFront Engine</p>
    </footer>
  </div>
</body>
</html>"""


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



def _build_context(spec: dict[str, Any], palette: Palette) -> dict[str, Any]:
    category = spec.get("category", "services")
    
    hero_image = {
        "food": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200",
        "apparel": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200",
        "electronics": "https://images.unsplash.com/photo-1519389950473-47ba0277781c?w=1200",
        "pharmacy": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=1200",
        "services": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=1200"
    }.get(category, "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1200")

    products = []
    for i, p in enumerate(spec.get("products", [])):
        p_copy = dict(p)
        p_copy["thumbnail"] = p.get("image_url") or _resolve_image_url(p.get("name", ""), category)
        products.append(p_copy)

    whatsapp = spec.get("contact", {}).get("whatsapp", "9876543210")

    return {
        "shop_name": spec["shop_name"],
        "category": category,
        "description": spec.get("description", "Welcome to our premier store."),
        "products": products,
        "hours": spec.get("hours", ["Mon-Sun: 9:00 AM - 9:00 PM"]),
        "location": spec.get("location"),
        "contact": spec.get("contact", {}),
        "whatsapp_number": whatsapp,
        "hero_image": hero_image,
        "primary": palette.primary,
        "secondary": palette.secondary,
        "accent": palette.accent,
        "text": palette.text,
        "background": palette.background,
    }


def _render_json_ld(spec: dict[str, Any]) -> str:
    schema_type = {
        "food": "FoodEstablishment",
        "apparel": "ClothingStore",
        "electronics": "ElectronicsStore",
        "pharmacy": "PharmacyOrDrugstore",
        "services": "LocalBusiness",
    }.get(spec["category"], "LocalBusiness")

    data = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": spec["shop_name"],
    }
    if spec.get("description"):
        data["description"] = spec["description"]
    if spec.get("contact", {}).get("whatsapp"):
        data["url"] = f"https://wa.me/{spec['contact']['whatsapp']}"
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def render(
    template_id: str,
    spec: dict[str, Any],
    palette: Palette,
) -> str:
    ctx = _build_context(spec, palette)
    try:
        template = _env.get_template(f"{template_id}.jinja2")
        template_ctx = {
            "shop_name": ctx["shop_name"],
            "category": ctx["category"],
            "description": ctx["description"],
            "products": ctx["products"],
            "hours": ctx["hours"],
            "location": ctx["location"],
            "contact": ctx["contact"],
            "colors": {
                "primary": palette.primary,
                "secondary": palette.secondary,
                "accent": palette.accent,
                "text": palette.text,
                "background": palette.background,
            }
        }
        return template.render(**template_ctx)
    except Exception:
        json_ld = _render_json_ld(spec)
        products_parts = ['<div class="section-title">Featured Catalog</div><div class="product-grid">']
        for p in ctx["products"]:
            products_parts.append(f"""
              <div class="product-card">
                <img src="{html.escape(p.get('thumbnail', ''))}" class="product-thumb" alt="{html.escape(p['name'])}" />
                <div class="product-info">
                  <h3>{html.escape(p['name'])}</h3>
                  <div class="desc">{html.escape(p.get('description', ''))}</div>
                  <div class="price">&#8377;{html.escape(str(p.get('price', 0)))}</div>
                </div>
              </div>
            """)
        products_parts.append('</div>')
        products_html = "".join(products_parts)

        hours_parts = ['<div class="section-title">Operating Hours</div><div class="info-card"><ul>']
        for h in ctx["hours"]:
            hours_parts.append(f"<li>{html.escape(h)}</li>")
        hours_parts.append('</ul></div>')
        hours_html = "".join(hours_parts)

        contact_parts = ['<div class="section-title">Location & Details</div><div class="info-card"><ul>']
        loc = ctx["location"]
        if loc:
            addr = f"{loc.get('address', '')}, {loc.get('city', '')}, {loc.get('state', '')} {loc.get('pincode', '')}".strip(", ")
            if addr:
                contact_parts.append(f"<li><strong>Address:</strong> {html.escape(addr)}</li>")
        phone = ctx["contact"].get("phone")
        if phone:
            contact_parts.append(f"<li><strong>Phone:</strong> {html.escape(phone)}</li>")
        contact_parts.append('</ul></div>')
        contact_html = "".join(contact_parts)

        return _PAGE_SHELL.format(
            shop_name=html.escape(ctx["shop_name"]),
            category=html.escape(ctx["category"]),
            description=html.escape(ctx["description"]),
            primary=palette.primary,
            secondary=palette.secondary,
            accent=palette.accent,
            text=palette.text,
            background=palette.background,
            json_ld=json_ld,
            hero_image=ctx["hero_image"],
            products_html=products_html,
            hours_html=hours_html,
            contact_html=contact_html,
            whatsapp_number=html.escape(str(ctx["whatsapp_number"])),
        )


def render_components(
    spec: dict[str, Any],
    palette: Palette,
    components: dict[str, dict[str, Any] | None],
) -> str:
    return render(spec.get("category", "services"), spec, palette)
