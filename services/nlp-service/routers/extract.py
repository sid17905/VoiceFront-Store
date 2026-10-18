from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from schemas.entity_types import StorefrontSpec, NlpExtractResponse
from core.schema_builder import extract_storefront_spec
from core.ner_model import NerEntityExtractor

router = APIRouter()
entity_extractor = NerEntityExtractor()


class ExtractRequestBody(BaseModel):
    prompt: Optional[str] = Field(default=None, description="Direct text prompt")
    transcript: Optional[str] = Field(default=None, description="Audio transcript (for backward compatibility)")
    language: Optional[str] = Field(default="en", description="Language code")
    shop_id: Optional[str] = Field(default=None, description="Shop identifier")


@router.post("/extract", response_model=NlpExtractResponse)
async def extract_nlp_metadata(body: ExtractRequestBody) -> NlpExtractResponse:
    raw_input = body.prompt or body.transcript
    if not raw_input or not raw_input.strip():
        raise HTTPException(status_code=400, detail={"error_code": "EMPTY_PROMPT", "message": "Prompt or transcript cannot be empty"})

    spec, is_valid, invalid_fields = await extract_storefront_spec(raw_input.strip())

    return NlpExtractResponse(
        storefront_spec=spec,
        is_valid=is_valid,
        raw_prompt=raw_input,
        invalid_fields=invalid_fields,
    )
