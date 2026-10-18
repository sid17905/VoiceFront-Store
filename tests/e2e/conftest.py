"""Bootstrap for the e2e suite.

Service packages are loaded per test through `tests/e2e/_loader.py`; this file
only makes the repo root and `packages/` importable and keeps sibling service
directories off `sys.path` so the namespace package `core` is not captured by
whichever service was imported first.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"

_service_dirs = {str(p.resolve()) for p in SERVICES.iterdir() if p.is_dir()}
sys.path[:] = [p for p in sys.path if str(Path(p).resolve()) not in _service_dirs]

for entry in (str(ROOT), str(ROOT / "packages"), str(Path(__file__).parent)):
    if entry not in sys.path:
        sys.path.insert(0, entry)
