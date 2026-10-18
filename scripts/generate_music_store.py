"""
scripts/generate_music_store.py

Generates a sample music store storefront using VoiceFront Store's layout and NLP engines.
"""

from __future__ import annotations
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "services" / "layout-service"))
sys.path.insert(0, str(root_dir / "packages" / "schemas"))
sys.path.insert(0, str(root_dir / "packages" / "common_utils"))

from entity_types import StorefrontSpec, StoreCategory, ProductItem, LocationInfo, ContactInfo
from core.renderer import render
from core.palette_engine import get_palette

def generate_music_store():
    spec = {
        "shop_name": "Rock & Melody Music Store",
        "category": "services",
        "description": "Your ultimate destination for guitars, drums, and professional audio gear.",
        "products": [
            {"name": "Acoustic Guitar", "price": 8500, "currency": "INR", "description": "Solid spruce top, warm acoustic tone"},
            {"name": "Electric Guitar", "price": 14999, "currency": "INR", "description": "Dual humbuckers, high-output rock sound"},
            {"name": "Professional Drum Kit", "price": 24999, "currency": "INR", "description": "5-piece maple shell kit with hardware"}
        ],
        "hours": ["Mon-Sat: 10:00 AM - 8:00 PM"],
        "location": {"address": "MG Road", "city": "Bangalore", "state": "Karnataka", "pincode": "560001"},
        "contact": {"phone": "+919876501234", "whatsapp": "9876501234", "email": "support@rockandmelody.in"}
    }

    palette = get_palette("services")
    html = render("services", spec, palette)
    
    out_path = root_dir / "docs" / "music_store_preview.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Music store website generated successfully! Saved to: {out_path}")
    print("\n--- HTML Preview ---")
    print(html[:400] + "\n...\n" + html[-300:])

if __name__ == "__main__":
    generate_music_store()
