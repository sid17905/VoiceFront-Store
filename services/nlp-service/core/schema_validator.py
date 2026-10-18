from __future__ import annotations

import json
from typing import Any, Tuple, List
from pydantic import ValidationError

import sys
from pathlib import Path
nlp_dir = Path(__file__).resolve().parents[1]
root_path = Path(__file__).resolve().parents[2]
if str(nlp_dir) not in sys.path:
    sys.path.insert(0, str(nlp_dir))
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from packages.schemas.entity_types import StorefrontSpec


def validate_storefront_spec(data: dict[str, Any] | str) -> Tuple[StorefrontSpec | None, bool, List[str]]:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            return None, False, [f"JSON decode error: {str(exc)}"]

    try:
        spec = StorefrontSpec(**data)
        return spec, True, []
    except ValidationError as exc:
        errors = [f"{e['loc']}: {e['msg']}" for e in exc.errors()]
        return None, False, errors
    except Exception as exc:
        return None, False, [str(exc)]
