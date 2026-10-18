"""Load a service's `core` package without the namespace collision.

Each service has a top-level `core/` directory with no `__init__.py`. Python
treats those as PEP 420 namespace packages, and a namespace package's
`__path__` is computed from every matching `sys.path` entry. Once any module
imports `core`, later services cannot extend that `__path__`, so
`core.schema_builder` resolves to whichever service imported first.

`load_core()` removes sibling service directories from `sys.path`, imports the
requested service's package, and returns the module. It also invalidates the
import caches so a previously cached namespace path is not reused.

This exists only until step A4 turns the packages into installed modules.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"


def _service_dirs() -> set[str]:
    return {
        str(p.resolve())
        for p in SERVICES.iterdir()
        if p.is_dir() and (p / "core").is_dir()
    }


def load_core(service: str, module: str):
    """Import `core.<module>` from `services/<service>`.

    Example: load_core("nlp-service", "schema_builder")
    """
    service_dir = (SERVICES / service).resolve()
    if not (service_dir / "core").is_dir():
        raise ImportError(f"{service_dir}/core does not exist")

    blocked = _service_dirs()
    sys.path[:] = [p for p in sys.path if str(Path(p).resolve()) not in blocked]
    for entry in (str(ROOT), str(ROOT / "packages")):
        if entry not in sys.path:
            sys.path.insert(0, entry)
    sys.path.insert(0, str(service_dir))

    for name in list(sys.modules):
        if name == "core" or name.startswith("core."):
            del sys.modules[name]
    importlib.invalidate_caches()

    return importlib.import_module(f"core.{module}")
