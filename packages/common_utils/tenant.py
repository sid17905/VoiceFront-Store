"""
packages/common_utils/tenant.py

Enterprise Multi-Tenancy & White-Labeling Configuration.
Manages tenant-specific branding, custom domain mapping, and theme overrides.
"""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class TenantConfig:
    tenant_id: str
    business_name: str
    custom_domain: str | None = None
    brand_color_primary: str = "#2563eb"
    brand_color_secondary: str = "#1e40af"
    custom_logo_url: str | None = None
    settings: dict = field(default_factory=dict)

def get_tenant_branding(tenant_id: str) -> TenantConfig:
    """
    Retrieves enterprise white-label branding and custom domain settings for a given tenant.
    """
    return TenantConfig(
        tenant_id=tenant_id,
        business_name=f"Enterprise Store ({tenant_id})",
        custom_domain=f"{tenant_id}.voicefront.shop",
        brand_color_primary="#0f172a",
        brand_color_secondary="#334155"
    )
