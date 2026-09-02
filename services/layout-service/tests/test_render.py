import sys
sys.path.insert(0, '.')

from core.palette_engine import get_palette
from core.template_classifier import select_template
from core.renderer import render

spec = {
    "shop_name": "Sharma General Store",
    "category": "food",
    "description": "Fresh groceries and daily needs.",
    "products": [
        {"name": "Rice", "price": 60, "description": "Per kg"},
        {"name": "Dal", "price": 120, "description": "Per kg"},
        {"name": "Oil", "price": 150, "description": "1 litre"},
    ],
    "hours": ["Mon-Sat 08:00-20:00", "Sun 10:00-16:00"],
    "location": {"raw_text": "MG Road, Pune", "lat": 18.52, "lng": 73.85, "location_verified": True},
    "contact": {"whatsapp": "919999999999", "phone": "919999999999"},
}

template_id = select_template(spec)
palette = get_palette(spec["category"])
html = render(template_id, spec, palette)

checks = {
    "template_id": template_id == "food",
    "html_length": len(html) > 500,
    "shop_name": "Sharma General Store" in html,
    "product": "Rice" in html,
    "price": "60" in html,
    "whatsapp_link": "wa.me/919999999999" in html,
    "json_ld": "application/ld+json" in html,
    "aria_label": "aria-label" in html,
    "viewport": "viewport" in html,
    "foodEstablishment": "FoodEstablishment" in html,
}

for name, passed in checks.items():
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}")

all_passed = all(checks.values())
print()
if all_passed:
    print("All checks passed!")
else:
    print("Some checks FAILED")
    sys.exit(1)
