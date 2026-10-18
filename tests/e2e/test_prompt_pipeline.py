import pytest
import sys
import importlib.util
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


@pytest.mark.asyncio
async def test_end_to_end_prompt_to_storefront():
    # 1. NLP extraction
    nlp_dir = root_dir / "services" / "nlp-service"
    sys.path.insert(0, str(nlp_dir))
    from core.schema_builder import extract_storefront_spec

    user_prompt = """
    Create an online store for The Daily Fresh Bakery.
    We offer Sourdough Bread for Rs 180, Chocolate Croissant at 120, and Blueberry Cheesecake for 250.
    Open Monday to Saturday 8 AM to 8 PM.
    Call us or WhatsApp at 9876543210. Located at Bandra West, Mumbai.
    """

    spec, is_valid, invalid_fields = await extract_storefront_spec(user_prompt)
    assert is_valid is True
    assert spec is not None
    assert spec.category.value == "food"
    assert len(spec.products) > 0

    # 2. Layout generation (isolate sys.path to layout-service)
    layout_dir = root_dir / "services" / "layout-service"
    if str(nlp_dir) in sys.path:
        sys.path.remove(str(nlp_dir))
    if "core" in sys.modules:
        del sys.modules["core"]
    sys.path.insert(0, str(layout_dir))

    from core.palette_engine import get_palette
    from core.template_classifier import select_template
    from core.renderer import render

    spec_dict = spec.model_dump()
    template_id = select_template(spec_dict)
    palette = get_palette(spec.category.value)

    # 3. Render HTML
    html = render(template_id, spec_dict, palette)

    # 4. Assertions
    assert "FoodEstablishment" in html or "LocalBusiness" in html
    assert spec.shop_name in html
    assert "wa.me/" in html
    assert 'name="viewport"' in html
    assert len(html) > 500
