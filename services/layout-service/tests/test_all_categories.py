import sys
sys.path.insert(0, ".")

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

all_passed = True
for category, expected_schema_type in CATEGORIES.items():
    spec = {**base_spec, "category": category}
    try:
        tid = select_template(spec)
        palette = get_palette(category)
        html = render(tid, spec, palette)
        has_schema = expected_schema_type in html
        has_products = "Item" in html
        has_wa = "wa.me" in html
        ok = tid == category and has_schema and has_products and has_wa
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {category} (schema={expected_schema_type}, len={len(html)})")
        if not ok:
            all_passed = False
    except Exception as e:
        print(f"  [FAIL] {category}: {e}")
        all_passed = False

print()
print("All categories passed!" if all_passed else "Some categories FAILED")
sys.exit(0 if all_passed else 1)
