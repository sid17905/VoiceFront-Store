from __future__ import annotations

from pathlib import Path

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
