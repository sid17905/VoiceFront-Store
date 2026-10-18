import sys
from pathlib import Path
layout_dir = Path(__file__).resolve().parents[1]
if str(layout_dir) != sys.path[0]:
    sys.path.insert(0, str(layout_dir))

if "core" in sys.modules and not hasattr(sys.modules["core"], "palette_engine"):
    del sys.modules["core"]

from core.palette_engine import get_palette
from core.template_classifier import select_template
from core.renderer import render

CATEGORIES = {
    "food": "FoodEstablishment",
    "apparel": "ClothingStore",
    "electronics": "ElectronicsStore",
    "pharmacy": "PharmacyOrDrugstore",
    "services": "LocalBusiness",
}

base_spec = {
    "shop_name": "Test Shop",
    "category": "",
    "description": "A test shop.",
    "products": [{"name": "Item", "price": 100, "description": "Test item"}],
    "hours": ["Mon-Fri 09:00-18:00"],
    "location": {"raw_text": "Test City"},
    "contact": {"whatsapp": "919999999999", "phone": "919999999999"},
}


def test_all_categories():
    for category, expected_schema_type in CATEGORIES.items():
        spec = {**base_spec, "category": category}
        tid = select_template(spec)
        palette = get_palette(category)
        html = render(tid, spec, palette)
        assert expected_schema_type in html
        assert "Item" in html
        assert "wa.me" in html
        assert tid == category
