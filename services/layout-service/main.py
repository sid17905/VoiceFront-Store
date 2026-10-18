"""layout-service — FastAPI application entry point."""

from __future__ import annotations

import os
import logging
import time
import uuid
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routers.generate import router as generate_router
from routers.scrape import router as scrape_router

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","service":"layout-service","request_id":"%(request_id)s","message":"%(message)s"}',
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app = FastAPI(
    title="VoiceFront Layout Service",
    version="2.0.0",
    docs_url="/docs" if os.getenv("ENV", "dev") != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

app.include_router(generate_router, prefix="/v1/layout", tags=["layout"])
app.include_router(scrape_router, prefix="/v1/layout", tags=["scrape"])


@app.middleware("http")
async def request_id_and_logging(request: Request, call_next: Callable) -> Response:
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    start = time.monotonic()
    response = await call_next(request)
    ms = round((time.monotonic() - start) * 1000, 1)
    logging.info(
        f"method={request.method} path={request.url.path} status={response.status_code} ms={ms}",
        extra={"request_id": request_id},
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", extra={"request_id": "?"})
    return JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR", "message": "An unexpected error occurred."})


@app.get("/health")
async def health_check() -> dict:
    from pathlib import Path
    template_dir = Path(__file__).parent / "templates"
    component_dir = Path(__file__).parent.parent.parent / "data" / "component-library"
    return {
        "status": "ok",
        "service": "layout-service",
        "version": "2.0.0",
        "templates_available": len(list(template_dir.glob("*.jinja2"))) if template_dir.exists() else 0,
        "components_available": len(list(component_dir.rglob("*.json"))) if component_dir.exists() else 0,
    }
