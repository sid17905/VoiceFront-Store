from __future__ import annotations

import os
import json
import logging
import re
import time
from typing import Any, Tuple, List

from schemas.entity_types import StorefrontSpec, StoreCategory
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

    # Build tagline: up to 8 words following a "named"/"called" marker.
    # The previous code used a character offset to slice a word list, which
    # produced arbitrary slices.
    words = prompt.split()
    lower_words = [w.lower().strip(".,:;!?") for w in words]
    start = 0
    for marker in ("named", "called"):
        if marker in lower_words:
            start = lower_words.index(marker) + 1
            break
    tagline = " ".join(words[start:start + 8]).strip(" .,")

    # Extract phone / whatsapp numbers
    phone_match = re.search(r"(?:\+?91[\-\s]?)?[6-9]\d{9}", prompt)
    contact: dict[str, str] = {}
    if phone_match:
        number = phone_match.group(0).replace(" ", "").replace("-", "")
        contact["phone"] = number
        contact["whatsapp"] = number

    # Extract products from explicit price mentions.
    # Two shapes occur in real prompts:
    #   "Sourdough Bread for Rs 180"   (keyword between name and price)
    #   "smart watches 2500"           (name then bare number)
    products: list[dict[str, Any]] = []
    keyword_pairs = re.findall(
        r"([A-Za-z][A-Za-z\s'&-]*?)\s+(?:for|at|costs?|price|rs\.?|inr)\s*"
        r"(?:rs\.?|inr)?\s*(\d+(?:\.\d+)?)",
        prompt, re.IGNORECASE,
    )
    bare_pairs = re.findall(
        r"([A-Za-z][A-Za-z\s'&-]{2,40}?)\s+(\d{2,7}(?:\.\d+)?)(?!\d)",
        prompt,
    )

    # Words that begin a clause rather than a product name.
    STOP_PREFIX = ("and", "we", "our", "with", "selling", "sells", "sell",
                   "open", "call", "contact", "whatsapp", "located", "near",
                   "in", "at", "for", "store", "shop", "the", "a", "an")
    BLOCK = {"we", "our", "call", "contact", "open", "located"}

    seen: set[str] = set()

    def add(name: str, price: str) -> None:
        clean = re.sub(r"\s+", " ", name).strip(" ,.-'&")
        words = clean.split()
        while words and words[0].lower() in STOP_PREFIX:
            words.pop(0)
        clean = " ".join(words)
        if len(clean) < 2 or len(clean.split()) > 6:
            return
        if any(w in clean.lower().split() for w in BLOCK):
            return
        key = clean.lower()
        if key in seen:
            return
        seen.add(key)
        products.append({
            "name": clean[0].upper() + clean[1:],
            "price": float(price),
            "currency": "INR",
            "description": f"{clean[0].upper() + clean[1:]} at {shop_name}",
            "is_suggested": False,
        })

    for name, price in keyword_pairs + bare_pairs:
        add(name, price)

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


async def extract_storefront_spec(prompt: str, api_key: str | None = None, model: str | None = None) -> Tuple[StorefrontSpec, bool, List[dict[str, str]]]:
    model = model or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    key = api_key or os.getenv("GROQ_API_KEY", "")

    def _fallback(reason: str = "") -> Tuple[StorefrontSpec, bool, List[dict[str, str]]]:
        fallback_data = _heuristic_fallback_extractor(prompt)
        spec, valid, errors = validate_storefront_spec(fallback_data)
        invalid = list(errors)
        if spec is None:
            invalid.append({"field": "category", "reason": "could not infer a category"})
            return (
                StorefrontSpec(shop_name="Retail Store", category=StoreCategory.SERVICES),
                False,
                invalid,
            )
        if not spec.products:
            valid = False
            invalid.append({"field": "products", "reason": "no priced product found"})
        if reason:
            invalid.append({"field": "llm", "reason": reason})
        return spec, valid, invalid

    if key.strip() in PLACEHOLDER_KEYS:
        logger.warning("NLP running in heuristic fallback mode — GROQ_API_KEY not set")
        return _fallback()

    try:
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
        from common_utils.groq_client import GroqNotConfigured, client as groq_client
    except ImportError:
        return _fallback("groq/tenacity not installed")

    try:
        client = groq_client()
    except GroqNotConfigured:
        return _fallback("GROQ_API_KEY is not configured")

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
            described = "; ".join(f"{e['field']}: {e['reason']}" for e in errors)
            messages.append({"role": "user", "content": f"Your previous response had schema validation errors: {described}. Please correct them and return the updated JSON."})
        except Exception as exc:
            logger.error(f"Groq LLM attempt {attempt+1} failed: {type(exc).__name__}")
            if attempt == 1:
                return _fallback(f"LLM call failed: {type(exc).__name__}")

    return _fallback("max validation attempts exceeded")
