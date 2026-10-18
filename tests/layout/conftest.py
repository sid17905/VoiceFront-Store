"""Test bootstrap for layout proofs.

Adds the layout-service package to sys.path so `core.*` imports resolve from the
repo root. This is the same bootstrap the service itself uses until A4 replaces
it with an installed package.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAYOUT = ROOT / "services" / "layout-service"
PACKAGES = ROOT / "packages"
for p in (str(LAYOUT), str(PACKAGES), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
