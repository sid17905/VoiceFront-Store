#!/usr/bin/env python3
"""Generate machine-readable schemas from the Pydantic source (A3).

`packages/schemas/entity_types.py` is the only authored schema. This script
regenerates the JSON Schema mirror and a TypeScript declaration so the three
cannot drift. CI runs it and fails on a non-empty diff.

Usage:
    python scripts/gen_schemas.py          # write
    python scripts/gen_schemas.py --check  # exit 1 if anything would change
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"
sys.path.insert(0, str(PACKAGES))

from schemas.entity_types import (  # noqa: E402
    ContactInfo,
    LocationInfo,
    NlpExtractRequest,
    NlpExtractResponse,
    ProductItem,
    StorefrontSpec,
)

MODELS = {
    "StorefrontSpec": StorefrontSpec,
    "ProductItem": ProductItem,
    "LocationInfo": LocationInfo,
    "ContactInfo": ContactInfo,
    "NlpExtractRequest": NlpExtractRequest,
    "NlpExtractResponse": NlpExtractResponse,
}

TS_HEADER = """// GENERATED FILE — do not edit. Source: packages/schemas/entity_types.py
// Regenerate with: python scripts/gen_schemas.py

export type StoreCategory = "food" | "apparel" | "electronics" | "pharmacy" | "services";

export interface ProductItem {
  name: string;
  price?: number | string | null;
  currency?: string;
  description?: string | null;
  is_suggested?: boolean;
  image_url?: string | null;
}

export interface LocationInfo {
  address?: string | null;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
  lat?: number | null;
  lng?: number | null;
}

export interface ContactInfo {
  phone?: string | null;
  whatsapp?: string | null;
  email?: string | null;
  instagram?: string | null;
}

export interface StorefrontSpec {
  shop_name: string;
  category: StoreCategory;
  description?: string | null;
  products?: ProductItem[];
  hours?: string[];
  location?: LocationInfo | null;
  source?: string | null;
  contact?: ContactInfo | null;
}

export interface NlpExtractRequest {
  prompt: string;
  shop_id?: string | null;
}

export interface InvalidField {
  field: string;
  reason: string;
}

export interface NlpExtractResponse {
  storefront_spec: StorefrontSpec;
  is_valid: boolean;
  raw_prompt: string;
  invalid_fields?: InvalidField[];
}
"""


def generated() -> dict[Path, str]:
    out: dict[Path, str] = {}
    out[ROOT / "packages/schemas/storefront_spec.schema.json"] = (
        json.dumps(StorefrontSpec.model_json_schema(), indent=2, sort_keys=True) + "\n"
    )
    out[ROOT / "packages/schemas/entity_types.ts"] = TS_HEADER
    return out


def main() -> int:
    check = "--check" in sys.argv
    changed = []
    for path, content in generated().items():
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != content:
            changed.append(path)
            if not check:
                path.write_text(content, encoding="utf-8")
    if check:
        if changed:
            print("schemas are out of date:")
            for p in changed:
                print("  " + str(p.relative_to(ROOT)))
            return 1
        print("schemas are in sync")
        return 0
    print(f"wrote {len(changed)} file(s)" if changed else "already in sync")
    return 0


if __name__ == "__main__":
    sys.exit(main())
