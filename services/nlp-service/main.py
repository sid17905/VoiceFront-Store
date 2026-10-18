from __future__ import annotations

from routers.extract import router as extract_router
from common_utils.groq_client import is_configured, model
from common_utils.security import SecurityMiddleware
from common_utils.service_app import create_app

def _health_extra() -> dict:
    return {
        "groq_api": "live" if is_configured() else "heuristic-fallback",
        "model": model("chat"),
    }


app = create_app("nlp-service", "2.0.0", health_extra=_health_extra)
app.add_middleware(SecurityMiddleware)
app.include_router(extract_router, prefix="/v1/nlp", tags=["nlp"])
