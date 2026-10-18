from __future__ import annotations

import json
from typing import Any, Tuple, List
from pydantic import ValidationError

from schemas.entity_types import StorefrontSpec


def validate_storefront_spec(data: dict[str, Any] | str) -> Tuple[StorefrontSpec | None, bool, List[dict[str, str]]]:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            return None, False, [{"field": "json", "reason": f"JSON decode error: {exc}"}]

    try:
        spec = StorefrontSpec(**data)
        return spec, True, []
    except ValidationError as exc:
        errors = [
            {"field": ".".join(str(part) for part in e["loc"]), "reason": e["msg"]}
            for e in exc.errors()
        ]
        return None, False, errors
    except Exception as exc:
        return None, False, [{"field": "spec", "reason": str(exc)}]
