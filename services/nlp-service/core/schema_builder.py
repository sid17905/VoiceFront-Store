from __future__ import annotations

import os
import json
import logging
import re
import time
from typing import Any, Tuple, List

import sys
from pathlib import Path
nlp_dir = Path(__file__).resolve().parents[1]
root_path = Path(__file__).resolve().parents[2]
if str(nlp_dir) not in sys.path:
    sys.path.insert(0, str(nlp_dir))
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from packages.schemas.entity_types import StorefrontSpec, StoreCategory, ProductItem, LocationInfo, ContactInfo
from core.schema_validator import validate_storefront_spec

logger = logging.getLogger(__name__)
PLACEHOLDER_KEYS = {"", "mock", "placeholder", "your_groq_api_key_here"}


SYSTEM_PROMPT = """You are an expert AI data extraction engine for VoiceFront-Store.
Your task is to extract structured retail storefront metadata from raw English text prompts or spoken transcripts.

You MUST return ONLY a strictly valid JSON object adhering to the following JSON schema:
{
  "shop_name": string (Name of shop/business, required),
  "category": "food" | "apparel" | "electronics" | "pharmacy" | "services" (Choose best fit, required),
  "description": string (Catchy tagline or short summary),
  "products": [
    {
      "name": string (Product or service name),
      "price": number or null (Price value),
      "currency": "INR" (or detected currency),
      "description": string (Optional item summary)
    }
  ],
  "hours": [string] (e.g. "Mon-Sat: 9:00 AM - 9:00 PM"),
  "location": {
    "address": string,
    "city": string,
    "state": string,
    "pincode": string
  },
  "contact": {
    "phone": string,
    "whatsapp": string,
    "email": string,
    "instagram": string
  }
}

Do not wrap output in markdown codeblocks if possible, or provide valid raw JSON.
Infer unspecified fields conservatively. Do not make up fake products if not mentioned.
"""


def _heuristic_fallback_extractor(prompt: str) -> dict[str, Any]:
    """Fallback extractor: returns spec dict with source "fallback"."""
    prompt_lower = prompt.lower()
    
    # Determine category (heuristic based on keywords)
    category = "services"
    if any(w in prompt_lower for w in ["food", "restaurant", "cafe", "pizza", "burger", "biryani", "bakery", "kitchen", "coffee", "sweet"]):
        category = "food"
    elif any(w in prompt_lower for w in ["cloth", "apparel", "wear", "shirt", "dress", "boutique", "fashion", "saree", "garment"]):
        category = "apparel"
    elif any(w in prompt_lower for w in ["electronic", "mobile", "laptop", "phone", "repair", "gadget", "charger", "tv"]):
        category = "electronics"
    elif any(w in prompt_lower for w in ["pharma", "chemist", "medicine", "drug", "healthcare", "medical", "clinic"]):
        category = "pharmacy"

    # Extract shop name
    shop_name = "My Retail Store"
    name_match = re.search(r"(?:called|named|is|name is|welcome to)\s+([A-Za-z0-9\s'&]+?)(?:\.|\,|$|and|\n|located)", prompt, re.IGNORECASE)
    if name_match:
        shop_name = name_match.group(1).strip()
    else:
        words = prompt.strip().split()
        if len(words) >= 2:
            shop_name = f"{words[0].capitalize()} {words[1].capitalize()}"

    # Locate city reference e.g. "in Mumbai"
    city_match = re.search(r"in\s+([A-Za-z\s]+?)(?:\.|,|$)", prompt, re.IGNORECASE)
    city = city_match.group(1).strip().title() if city_match else None

    # Build tagline: first 8 words after shop name, capped at 8 words
    words = prompt.split()
    if "named" in prompt_lower:
        idx = prompt_lower.index("named") + 5  # approximate start after 'named'
        tagline_words = words[idx:idx+8]
    else:
        tagline_words = words[:8]
    tagline = ' '.join(tagline_words)

    # Extract phone / whatsapp numbers
    phone_match = re.search(r"(?:\+?91[\-\s]?)?[6-9]\d{9}", prompt)
    contact: dict[str, str] = {}
    if phone_match:
        number = phone_match.group(0).replace(" ", "").replace("-", "")
        contact["phone"] = number
        contact["whatsapp"] = number

    # Extract prices & products from explicit price mentions
    products: list[dict[str, Any]] = []
    product_matches = re.findall(r"([A-Za-z\s]+?)\s+(?:for|at|costs?|price|rs\.?|inr)\s*(?:rs\.?|inr)?\s*(\d+(?:\.\d+)?)", prompt, re.IGNORECASE)
    for prod_name, price in product_matches:
        clean_name = prod_name.strip()
        if len(clean_name) > 1 and not any(w in clean_name.lower() for w in ["we", "our", "call", "contact", "open", "at"]):
            products.append({
                "name": clean_name.capitalize(),
                "price": float(price),
                "currency": "INR",
                "description": f"Fresh {clean_name}",
                "is_suggested": False
            })

    return {
        "shop_name": shop_name,
        "category": category,
        "description": tagline,
        "products": products,
        "hours": [],
        "location": {"city": city} if city else None,
        "contact": contact if contact else {},
        "source": "fallback"
    }


async def extract_storefront_spec(prompt: str, api_key: str | None = None, model: str = "llama-3.3-70b-versatile") -> Tuple[StorefrontSpec, bool, List[str]]:
    key = api_key or os.getenv("GROQ_API_KEY", "")
    if key.strip() in PLACEHOLDER_KEYS:
        logger.warning("NLP running in heuristic fallback mode — GROQ_API_KEY not set")
        fallback_data = _heuristic_fallback_extractor(prompt)
        spec, valid, errors = validate_storefront_spec(fallback_data)
        invalid_fields = list(errors)
        if not spec or not spec.products:
            valid = False
            invalid_fields.append("products")
        return spec if spec else StorefrontSpec(shop_name="Retail Store", category=StoreCategory.FOOD), valid, invalid_fields

    try:
        from groq import Groq
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    except ImportError:
        fallback_data = _heuristic_fallback_extractor(prompt)
        spec, valid, errors = validate_storefront_spec(fallback_data)
        return spec if spec else StorefrontSpec(shop_name="Retail Store", category=StoreCategory.FOOD), valid, errors

    client = Groq(api_key=key)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract the StorefrontSpec for this input:\n\n{prompt}"}
    ]

    for attempt in range(2):
        try:
            t0 = time.monotonic()

            @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=6), reraise=True)
            def _call():
                return client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )

            chat_completion = _call()
            ms = round((time.monotonic() - t0) * 1000, 1)
            logger.info(f"Groq LLM extraction attempt {attempt+1} complete in {ms}ms")

            raw_text = chat_completion.choices[0].message.content or "{}"
            parsed_json = json.loads(raw_text)
            spec, valid, errors = validate_storefront_spec(parsed_json)
            if valid and spec is not None:
                return spec, True, []

            messages.append({"role": "assistant", "content": raw_text})
            messages.append({"role": "user", "content": f"Your previous response had schema validation errors: {', '.join(errors)}. Please correct them and return the updated JSON."})
        except Exception as exc:
            logger.error(f"Groq LLM attempt {attempt+1} failed: {exc}")
            if attempt == 1:
                fallback_data = _heuristic_fallback_extractor(prompt)
                spec, valid, errors = validate_storefront_spec(fallback_data)
                return spec if spec else StorefrontSpec(shop_name="Retail Store", category=StoreCategory.FOOD), False, [str(exc)]

    fallback_data = _heuristic_fallback_extractor(prompt)
    spec, valid, errors = validate_storefront_spec(fallback_data)
    return spec if spec else StorefrontSpec(shop_name="Retail Store", category=StoreCategory.FOOD), False, ["Max validation attempts exceeded"]
