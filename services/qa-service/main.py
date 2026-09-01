"""
services/qa-service/main.py — FastAPI entrypoint.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routers.qa import router as qa_router

try:
    from common_utils.exceptions import QaViolationError
except ImportError:  # pragma: no cover
    class QaViolationError(Exception):
        def __init__(self, error_code: str, message: str):
            self.error_code = error_code
            self.message = message
            super().__init__(f"{error_code}: {message}")

app = FastAPI(title="qa-service", version="0.1.0")
app.include_router(qa_router)


@app.exception_handler(QaViolationError)
async def qa_violation_error_handler(request: Request, exc: QaViolationError):
    # api_contracts.md: 500 QaViolationError — reserved for pipeline failure
    # (Playwright crash, FAISS unreachable), never for "violations found."
    return JSONResponse(status_code=500, content=exc.to_dict() if hasattr(exc, "to_dict") else {
        "error_code": exc.error_code, "message": exc.message,
    })


@app.get("/health")
def health():
    return {"status": "ok", "service": "qa-service"}
