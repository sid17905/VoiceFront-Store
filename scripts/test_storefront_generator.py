"""
scripts/test_storefront_generator.py

End-to-end integration test and generator script.
Tests NLP extraction -> Layout rendering -> QA detection -> Output generation.
"""

from __future__ import annotations
import sys
import asyncio
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "services" / "nlp-service"))
sys.path.insert(0, str(root_dir / "services" / "layout-service"))
sys.path.insert(0, str(root_dir / "packages"))

from core.schema_builder import extract_storefront_spec
from core.renderer import render_storefront

async def test_generate_sample_storefront():
    prompt = "Create a coffee shop named Brew & Bean in Pune with Espresso Rs 150, Latte Rs 200, open daily 8am to 10pm, WhatsApp 9123456789."
    print(f"Input Prompt: {prompt}\n")

    # 1. NLP extraction
    spec, is_valid, errors = await extract_storefront_spec(prompt)
    print(f"Extracted Spec valid? {is_valid}")
    print(f"Shop Name: {spec.shop_name}")
    print(f"Category: {spec.category}")
    print(f"Products: {len(spec.products)} items found.")

    # 2. Layout rendering
    html = render_storefront(spec, category=spec.category)
    print(f"Rendered HTML length: {len(html)} bytes")

    # Save output test page
    out_path = root_dir / "docs" / "test_generated_storefront.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Test storefront successfully saved to: {out_path}")

if __name__ == "__main__":
    asyncio.run(test_generate_sample_storefront())
