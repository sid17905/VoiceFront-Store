from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class StoreCategory(str, Enum):
    FOOD = "food"
    APPAREL = "apparel"
    ELECTRONICS = "electronics"
    PHARMACY = "pharmacy"
    SERVICES = "services"


class ProductItem(BaseModel):
    name: str = Field(..., description="Name of the product or service")
    price: Optional[float | str] = Field(default=None, description="Price in designated currency")
    currency: str = Field(default="INR", description="Currency symbol or ISO code")
    description: Optional[str] = Field(default=None, description="Item summary")
    is_suggested: bool = Field(default=False, description="Whether product was automatically suggested")
    image_url: Optional[str] = Field(default=None, description="URL to product image")


class LocationInfo(BaseModel):
    address: Optional[str] = Field(default=None, description="Street address")
    city: Optional[str] = Field(default=None, description="City")
    state: Optional[str] = Field(default=None, description="State / Province")
    pincode: Optional[str] = Field(default=None, description="Postal / PIN code")
    lat: Optional[float] = Field(default=None, description="Latitude")
    lng: Optional[float] = Field(default=None, description="Longitude")


class ContactInfo(BaseModel):
    phone: Optional[str] = Field(default=None, description="Primary phone number")
    whatsapp: Optional[str] = Field(default=None, description="WhatsApp contact number")
    email: Optional[str] = Field(default=None, description="Contact email address")
    instagram: Optional[str] = Field(default=None, description="Instagram handle")


class StorefrontSpec(BaseModel):
    shop_name: str = Field(..., min_length=1, description="Name of the retail storefront")
    category: StoreCategory = Field(..., description="Retail business category")
    description: Optional[str] = Field(default="", description="Tagline or store description")
    products: List[ProductItem] = Field(default_factory=list, description="Extracted product list")
    hours: List[str] = Field(default_factory=list, description="Formatted opening hours")
    location: Optional[LocationInfo] = Field(default=None, description="Store location")
    source: Optional[str] = Field(default=None, description="Source of the spec: 'groq' or 'fallback'")
    contact: Optional[ContactInfo] = Field(default_factory=ContactInfo, description="Contact info")


class ExtractedEntities(BaseModel):
    shop_name: Optional[str] = None
    category: Optional[str] = None
    products: List[dict[str, Any]] = Field(default_factory=list)
    contact: Optional[dict[str, str]] = None
    location: Optional[dict[str, Any]] = None
    hours: List[str] = Field(default_factory=list)


class NlpExtractRequest(BaseModel):
    prompt: str = Field(..., description="Raw English text prompt or speech transcript")
    shop_id: Optional[str] = Field(default=None, description="Optional shop identifier")


class NlpExtractResponse(BaseModel):
    storefront_spec: StorefrontSpec
    is_valid: bool = True
    raw_prompt: str
    invalid_fields: List[str] = Field(default_factory=list)
