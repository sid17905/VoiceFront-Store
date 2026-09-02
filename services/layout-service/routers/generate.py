"""
generate.py — POST /v1/layout/generate

Wires template_classifier → palette_engine → renderer.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.palette_engine import get_palette
from core.renderer import render
from core.template_classifier import select_template

router = APIRouter()


class StorefrontSpecInput(BaseModel):
    shop_name: str
    category: str
    description: str | None = None
    products: list[dict[str, Any]] = []
    hours: list[str] = []
    location: dict[str, Any] | None = None
    contact: dict[str, str] = {}


class StorefrontBundle(BaseModel):
    template_id: str
    html: str


class LayoutErrorResponse(BaseModel):
    error_code: str
    message: str


@router.post(
    "/generate",
    response_model=StorefrontBundle,
    responses={
        422: {"model": LayoutErrorResponse},
        500: {"model": LayoutErrorResponse},
    },
)
async def generate_layout(spec: StorefrontSpecInput) -> StorefrontBundle:
    spec_dict = spec.model_dump()

    try:
        template_id = select_template(spec_dict)
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "LAYOUT_NO_TEMPLATE_MATCH",
                "message": str(exc),
            },
        )

    try:
        palette = get_palette(spec.category)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "LAYOUT_NO_TEMPLATE_MATCH",
                "message": str(exc),
            },
        )

    try:
        html = render(template_id, spec_dict, palette)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "LAYOUT_RENDER_FAILED",
                "message": str(exc),
            },
        )

    return StorefrontBundle(template_id=template_id, html=html)
