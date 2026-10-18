// GENERATED FILE — do not edit. Source: packages/schemas/entity_types.py
// Regenerate with: python scripts/gen_schemas.py

export type StoreCategory = "food" | "apparel" | "electronics" | "pharmacy" | "services";

export interface ProductItem {
  name: string;
  price?: number | string | null;
  currency?: string;
  description?: string | null;
  is_suggested?: boolean;
  image_url?: string | null;
}

export interface LocationInfo {
  address?: string | null;
  city?: string | null;
  state?: string | null;
  pincode?: string | null;
  lat?: number | null;
  lng?: number | null;
}

export interface ContactInfo {
  phone?: string | null;
  whatsapp?: string | null;
  email?: string | null;
  instagram?: string | null;
}

export interface StorefrontSpec {
  shop_name: string;
  category: StoreCategory;
  description?: string | null;
  products?: ProductItem[];
  hours?: string[];
  location?: LocationInfo | null;
  source?: string | null;
  contact?: ContactInfo | null;
}

export interface NlpExtractRequest {
  prompt: string;
  shop_id?: string | null;
}

export interface InvalidField {
  field: string;
  reason: string;
}

export interface NlpExtractResponse {
  storefront_spec: StorefrontSpec;
  is_valid: boolean;
  raw_prompt: string;
  invalid_fields?: InvalidField[];
}
