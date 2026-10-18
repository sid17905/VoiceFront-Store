import pytest
import time
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from _loader import load_core  # noqa: E402


@pytest.mark.asyncio
async def test_ttl_stopwatch():
    start = time.monotonic()

    schema_builder = load_core("nlp-service", "schema_builder")
    spec, is_valid, _ = await schema_builder.extract_storefront_spec(
        "Coffee shop named Bean Counter selling espresso for 150"
    )

    palette_engine = load_core("layout-service", "palette_engine")
    renderer = load_core("layout-service", "renderer")

    palette = palette_engine.get_palette(spec.category.value)
    html = renderer.render(spec.category.value, spec.model_dump(), palette)

    elapsed = time.monotonic() - start
    print(f"End-to-end pipeline TTL Stopwatch: {elapsed:.3f} seconds")

    assert elapsed < 15.0
    assert len(html) > 100
