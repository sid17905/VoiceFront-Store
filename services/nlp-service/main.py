from __future__ import annotations

import os
import logging
import time
import uuid
from typing import Callable

import sys
from pathlib import Path
root_path = Path(__file__).resolve().parents[2]
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers.extract import router as extract_router

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","service":"nlp-service","request_id":"%(request_id)s","message":"%(message)s"}',
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app = FastAPI(
    title="VoiceFront NLP Service",
    description="Prompt-first Intent and Metadata Extraction Service",
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

app.include_router(extract_router, prefix="/v1/nlp", tags=["nlp"])


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
async def health():
    groq_key = os.getenv("GROQ_API_KEY", "")
    has_key = bool(groq_key) and groq_key not in ("mock", "placeholder", "your_groq_api_key_here")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return {
        "status": "ok",
        "service": "nlp-service",
        "version": "2.0.0",
        "groq_api": "live" if has_key else "heuristic-fallback",
        "model": model,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
