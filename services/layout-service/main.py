"""
layout-service — FastAPI application entry point.

Layout layer (L4) of the VoiceStorefront pipeline:
StorefrontSpec JSON -> HTML/CSS/JS bundle.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.generate import router as generate_router
from routers.scrape import router as scrape_router

app = FastAPI(
    title="VoiceFront Layout Service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate_router, prefix="/v1/layout", tags=["layout"])
app.include_router(scrape_router, prefix="/v1/layout", tags=["scrape"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
