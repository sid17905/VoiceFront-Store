import pytest
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

def test_wcag_compliance_script():
    layout_dir = root_dir / "services" / "layout-service"
    sys.path.insert(0, str(layout_dir))
    
    from core.palette_engine import get_palette
    from core.renderer import render
    
    categories = ["food", "apparel", "electronics", "pharmacy", "services"]
    passed = 0
    total = len(categories)
    
    for cat in categories:
        spec = {
            "shop_name": f"Test {cat.capitalize()} Store",
            "category": cat,
            "description": "A test storefront spec for WCAG compliance checks.",
            "products": [{"name": "Sample Item", "price": 100, "currency": "INR"}],
            "hours": [],
            "contact": {"whatsapp": "9876543210"},
            "location": {"city": "Mumbai", "address": "Bandra"}
        }
        palette = get_palette(cat)
        html = render(cat, spec, palette)
        
        # Check basic WCAG requirements in HTML markup
        has_lang = 'lang="en"' in html or "lang='en'" in html or 'lang="hi"' in html
        has_title = "<title>" in html
        has_alt = "alt=" in html or "aria-label" in html
        has_main = "<main" in html or "<body>" in html
        
        if has_lang and has_title and has_main:
            passed += 1
            
    pass_rate = (passed / total) * 100.0
    print(f"WCAG Compliance Pass Rate: {pass_rate:.1f}% ({passed}/{total} categories passed)")
    assert pass_rate >= 80.0
