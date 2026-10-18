import pytest
import sys
import importlib.util
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from _loader import load_core  # noqa: E402  (tests/e2e is on sys.path via conftest)


@pytest.mark.asyncio
async def test_end_to_end_prompt_to_storefront():
    # 1. NLP extraction
    schema_builder = load_core("nlp-service", "schema_builder")
    extract_storefront_spec = schema_builder.extract_storefront_spec

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

    # 2. Layout generation — load layout's own `core` package.
    palette_engine = load_core("layout-service", "palette_engine")
    template_classifier = load_core("layout-service", "template_classifier")
    renderer = load_core("layout-service", "renderer")

    spec_dict = spec.model_dump()
    template_id = template_classifier.select_template(spec_dict)
    palette = palette_engine.get_palette(spec.category.value)

    # 3. Render HTML
    html = renderer.render(template_id, spec_dict, palette)

    # 4. Assertions
    assert "FoodEstablishment" in html or "LocalBusiness" in html
    assert spec.shop_name in html
    assert "wa.me/" in html
    assert 'name="viewport"' in html
    assert len(html) > 500
