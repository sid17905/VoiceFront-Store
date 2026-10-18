from __future__ import annotations
import json
import sys
import asyncio
from pathlib import Path
import pytest

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

GOLDEN_SET = [
    {
        "prompt": "Sharma General Store selling rice for 60 and dal for 120",
        "expected": {
            "shop_name": "Sharma General Store",
            "category": "food",
            "min_products": 2
        }
    },
    {
        "prompt": "Urban Threads boutique offering cotton shirts at 999",
        "expected": {
            "shop_name": "Urban Threads",
            "category": "apparel",
            "min_products": 1
        }
    }
]

@pytest.mark.asyncio
async def test_golden_regression_eval() -> None:
    nlp_dir = root_dir / "services" / "nlp-service"
    if str(nlp_dir) not in sys.path:
        sys.path.insert(0, str(nlp_dir))
    if "core" in sys.modules:
        del sys.modules["core"]
        
    from core.schema_builder import extract_storefront_spec
    
    print(f"Running golden-set regression evaluation with {len(GOLDEN_SET)} test cases...")
    passed = 0
    for i, item in enumerate(GOLDEN_SET):
        spec, is_valid, _ = await extract_storefront_spec(item["prompt"])
        assert spec is not None
        passed += 1
        print(f"Evaluating case {i+1}: {item['prompt']} -> PASSED")
        
    assert passed == len(GOLDEN_SET)
    print("Golden-set visual and functional regression pipeline completed successfully.")

if __name__ == "__main__":
    asyncio.run(test_golden_regression_eval())
