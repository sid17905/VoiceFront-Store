"""
template_classifier.py — Maps a StorefrontSpec to a template ID.

Phase 1 stub: always returns the category field from the spec directly.
Phase 3 upgrade: TF-IDF vector of shop description → k-NN against
category templates (real classification, not just passthrough).

The category value is trusted to be one of the 5 valid enum values
because the StorefrontSpec has already been validated by nlp-service
before reaching this point.
"""

from __future__ import annotations

from typing import Any


def select_template(spec: dict[str, Any]) -> str:
    """Return the template ID for the given StorefrontSpec.

    Args:
        spec: A validated StorefrontSpec dict (already schema-validated).

    Returns:
        Template ID string matching one of the template filenames
        (without .jinja2 extension): food, apparel, electronics,
        pharmacy, or services.
    """
    return spec["category"]
