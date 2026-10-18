from __future__ import annotations

import sys
from pathlib import Path

# Make `common_utils` importable when the service is run directly from its own
# directory (the container sets WORKDIR to the service). Step A4 replaces this
# with installed packages.
_packages = Path(__file__).resolve().parents[2] / "packages"
if str(_packages) not in sys.path:
    sys.path.insert(0, str(_packages))

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
