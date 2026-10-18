from __future__ import annotations

import sys
from pathlib import Path

# Make `common_utils` importable when the service is run directly from its own
# directory (the container sets WORKDIR to the service). Step A4 replaces this
# with installed packages.
_packages = Path(__file__).resolve().parents[2] / "packages"
if str(_packages) not in sys.path:
    sys.path.insert(0, str(_packages))

from routers.generate import router as generate_router
from routers.scrape import router as scrape_router
from common_utils.security import SecurityMiddleware
from common_utils.service_app import create_app

def _health_extra() -> dict:
    templates = Path(__file__).resolve().parent / "templates"
    components = Path(__file__).resolve().parents[2] / "data" / "component-library"
    return {
        "templates_available": len(list(templates.glob("*.jinja2"))) if templates.exists() else 0,
        "components_available": len(list(components.rglob("*.json"))) if components.exists() else 0,
    }


app = create_app("layout-service", "2.0.0", health_extra=_health_extra)
app.add_middleware(SecurityMiddleware)
app.include_router(generate_router, prefix="/v1/layout", tags=["layout"])
app.include_router(scrape_router, prefix="/v1/layout", tags=["scrape"])
