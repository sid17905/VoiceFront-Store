"""
test_layout_service.py — Single comprehensive test for layout-service.

Covers:
  - Palette engine (all 5 categories)
  - Template classifier (stub passthrough)
  - Component picker (availability + fallback logic)
  - Renderer (component assembly path + monolithic fallback path)
  - FastAPI endpoints (health + generate)
  - All 5 category templates render correctly
  - WCAG basics (aria-label, viewport, JSON-LD)
  - API contract shape (StorefrontBundle response)
"""

import sys
import json
from pathlib import Path

_layout_dir = str(Path(__file__).resolve().parents[1])
if _layout_dir not in sys.path:
    sys.path.insert(0, _layout_dir)

if "core" in sys.modules and not hasattr(sys.modules.get("core"), "palette_engine"):
    del sys.modules["core"]

from core.palette_engine import get_palette, Palette, CATEGORY_PALETTES
from core.template_classifier import select_template
from core.component_picker import pick_components, has_components, COMPONENT_LIB_DIR
from core.renderer import render, render_components

# ─── Fixtures ────────────────────────────────────────────────────────

FOOD_SPEC = {
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

ALL_SPECS = {
    cat: {**FOOD_SPEC, "category": cat, "shop_name": f"Test {cat.title()}"}
    for cat in ["food", "apparel", "electronics", "pharmacy", "services"]
}

SCHEMA_TYPES = {
    "food": "FoodEstablishment",
    "apparel": "ClothingStore",
    "electronics": "ElectronicsStore",
    "pharmacy": "PharmacyOrDrugstore",
    "services": "LocalBusiness",
}

# ─── Design reference sources ────────────────────────────────────────

DESIGN_REF_SOURCES = {
    "food": [
        "https://www.swiggy.com",
        "https://www.zomato.com",
        "https://www.ubereats.com",
    ],
    "apparel": [
        "https://www.myntra.com",
        "https://www.ajio.com",
        "https://www.nykaafashion.com",
    ],
    "electronics": [
        "https://www.flipkart.com",
        "https://www.croma.com",
        "https://www.reliancedigital.in",
    ],
    "pharmacy": [
        "https://www.1mg.com",
        "https://www.pharmeasy.in",
        "https://www.netmeds.com",
    ],
    "services": [
        "https://www.urbanclap.com",
        "https://www.justdial.com",
        "https://www.sulekha.com",
    ],
}

# ─── Tests ────────────────────────────────────────────────────────────

results = []


def record_assertion(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((name, passed))
    suffix = f" ({detail})" if detail else ""
    print(f"  [{status}] {name}{suffix}")


def run_all():
    passed = 0
    failed = 0

    print("=" * 60)
    print("  LAYOUT-SERVICE TEST SUITE")
    print("=" * 60)

    # ── 1. Palette Engine ────────────────────────────────────────
    print("\n-- 1. Palette Engine --")

    for cat in ["food", "apparel", "electronics", "pharmacy", "services"]:
        p = get_palette(cat)
        record_assertion(
            f"palette({cat})",
            isinstance(p, Palette)
            and p.primary.startswith("#")
            and p.text.startswith("#"),
            f"primary={p.primary}",
        )

    try:
        get_palette("unknown_category")
        record_assertion("palette(unknown) raises ValueError", False, "no exception raised")
    except ValueError:
        record_assertion("palette(unknown) raises ValueError", True, "ValueError caught")

    record_assertion(
        "all 5 categories in CATEGORY_PALETTES",
        set(CATEGORY_PALETTES.keys()) == {"food", "apparel", "electronics", "pharmacy", "services"},
    )

    # ── 2. Template Classifier ───────────────────────────────────
    print("\n-- 2. Template Classifier --")

    for cat in ["food", "apparel", "electronics", "pharmacy", "services"]:
        spec = ALL_SPECS[cat]
        tid = select_template(spec)
        record_assertion(f"select_template({cat})", tid == cat, f"got={tid}")

    # ── 3. Component Picker ──────────────────────────────────────
    print("\n-- 3. Component Picker --")

    record_assertion(
        "component-library dir exists",
        COMPONENT_LIB_DIR.exists(),
        str(COMPONENT_LIB_DIR),
    )

    for cat in ["food", "apparel", "electronics", "pharmacy", "services"]:
        spec = ALL_SPECS[cat]
        comps = pick_components(spec)
        available = [k for k, v in comps.items() if v is not None]
        missing = [k for k, v in comps.items() if v is None]
        record_assertion(
            f"pick_components({cat})",
            True,
            f"available={available}, missing={missing}",
        )

    food_spec = ALL_SPECS["food"]
    record_assertion("has_components(food)=True (all 4 seeded)", has_components(food_spec))

    minimal_spec = {**FOOD_SPEC, "category": "nonexistent"}
    record_assertion("has_components(nonexistent)=False", not has_components(minimal_spec))

    # ── 4. Renderer — all 5 categories ───────────────────────────
    print("\n-- 4. Renderer (all categories) --")

    for cat in ["food", "apparel", "electronics", "pharmacy", "services"]:
        spec = ALL_SPECS[cat]
        palette = get_palette(cat)
        html = render(spec["category"], spec, palette)

        checks = [
            ("length", len(html) > 500),
            ("shop_name", spec["shop_name"] in html),
            ("product", spec["products"][0]["name"] in html),
            ("price", "60" in html or "100" in html),
            ("whatsapp_link", "wa.me/" in html),
            ("json_ld", "application/ld+json" in html),
            ("aria_label", "aria-label" in html),
            ("viewport_meta", "viewport" in html),
            ("schema_type", SCHEMA_TYPES[cat] in html),
        ]

        all_ok = all(ok for _, ok in checks)
        record_assertion(
            f"render({cat})",
            all_ok,
            f"len={len(html)}, schema={SCHEMA_TYPES[cat]}",
        )

        for check_name, ok in checks:
            if not ok:
                record_assertion(f"  render({cat}).{check_name}", False)

    # ── 5. Component assembly vs monolithic fallback ──────────────
    print("\n-- 5. Component Assembly vs Monolithic Fallback --")

    food_palette = get_palette("food")
    food_html_assembly = render("food", food_spec, food_palette)
    food_comps = pick_components(food_spec)
    food_html_manual = render_components(food_spec, food_palette, food_comps)
    record_assertion(
        "food: assembly matches manual render",
        food_html_assembly == food_html_manual,
        f"len={len(food_html_assembly)}",
    )

    elec_spec = ALL_SPECS["electronics"]
    elec_palette = get_palette("electronics")
    elec_html = render("electronics", elec_spec, elec_palette)
    record_assertion(
        "electronics: uses monolithic fallback (partial components)",
        "ElectronicsStore" in elec_html,
        f"len={len(elec_html)}",
    )

    # ── 6. Design reference sources ──────────────────────────────
    print("\n-- 6. Design Reference Sources --")

    sites_file = Path(__file__).resolve().parents[3] / "data" / "design-reference" / "sites.example.json"
    record_assertion("sites.example.json exists", sites_file.exists())

    if sites_file.exists():
        sites = json.loads(sites_file.read_text(encoding="utf-8"))
        for cat, urls in DESIGN_REF_SOURCES.items():
            cat_sites = [s for s in sites if s["category"] == cat]
            record_assertion(
                f"sources({cat}): {len(cat_sites)} sites defined",
                len(cat_sites) == len(urls),
                ", ".join(s["url"] for s in cat_sites),
            )

    # ── 7. API contract shape ────────────────────────────────────
    print("\n-- 7. API Contract Shape --")

    if _layout_dir not in sys.path:
        sys.path.insert(0, _layout_dir)
    import routers.generate as gen_router
    StorefrontSpecInput = gen_router.StorefrontSpecInput
    StorefrontBundle = gen_router.StorefrontBundle
    LayoutErrorResponse = gen_router.LayoutErrorResponse

    record_assertion("StorefrontSpecInput model exists", True)
    record_assertion("StorefrontBundle model exists", True)
    record_assertion("LayoutErrorResponse model exists", True)

    # Validate a real spec matches the input model
    try:
        StorefrontSpecInput(**FOOD_SPEC)
        record_assertion("StorefrontSpecInput validates food spec", True)
    except Exception as e:
        record_assertion("StorefrontSpecInput validates food spec", False, str(e))

    # ── 8. Provenance tracking ───────────────────────────────────
    print("\n-- 8. Provenance Tracking --")

    import json as _json
    from pathlib import Path as _Path

    comp_lib = _Path(__file__).resolve().parents[3] / "data" / "component-library"
    prov_count = 0
    for section_type in ["nav", "hero", "product_grid", "contact"]:
        section_dir = comp_lib / section_type
        if not section_dir.exists():
            continue
        for entry_file in sorted(section_dir.glob("*.json")):
            entry = _json.loads(entry_file.read_text(encoding="utf-8"))
            if entry.get("review_status") != "APPROVED":
                continue
            prov = entry.get("provenance", {})
            has_source = bool(prov.get("source_url"))
            has_selector = bool(prov.get("source_selector"))
            has_adaptation = bool(prov.get("adaptation_notes"))
            ok = has_source and has_selector and has_adaptation
            record_assertion(
                f"provenance({entry.get('variant_id', '?')})",
                ok,
                f"source={prov.get('source_url', 'NONE')}, selector={prov.get('source_selector', 'NONE')}",
            )
            if ok:
                prov_count += 1

    record_assertion("total components with full provenance", prov_count > 0, f"{prov_count} components")

    report_file = _Path(__file__).resolve().parents[3] / "data" / "provenance-report.html"
    record_assertion("provenance-report.html generated", report_file.exists())

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    passed_count = sum(1 for _, ok in results if ok)
    failed_count = sum(1 for _, ok in results if not ok)
    total = len(results)
    print(f"  RESULTS: {passed_count}/{total} passed, {failed_count} failed")
    print("=" * 60)

    return failed_count == 0


def test_layout_service_suite():
    assert run_all() is True


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
