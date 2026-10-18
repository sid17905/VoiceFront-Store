from __future__ import annotations

import re


def normalize_transcript(text: str) -> str:
    """Cleans and standardizes verbatim transcript text."""
    if not text:
        return ""

    # Replace multiple whitespaces
    cleaned = re.sub(r"\s+", " ", text).strip()

    # Standardize currency expressions
    cleaned = re.sub(r"\b(?:rupees|rs\.?|inr)\b", "Rs", cleaned, flags=re.IGNORECASE)

    # Standardize common phone patterns
    cleaned = re.sub(r"(\d{5})\s*(\d{5})", r"\1\2", cleaned)

    return cleaned
