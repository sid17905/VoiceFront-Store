from __future__ import annotations

from pathlib import Path

from routers.qa import router as qa_router
from common_utils.security import SecurityMiddleware
from common_utils.service_app import create_app

def _health_extra() -> dict:
    rules = Path(__file__).resolve().parents[2] / "data" / "constraint-rules"
    return {"rules_loaded": len(list(rules.glob("*.json"))) if rules.exists() else 0}


app = create_app("qa-service", "2.0.0", health_extra=_health_extra)
app.add_middleware(SecurityMiddleware)
app.include_router(qa_router)
