export type StoreCategory = "food" | "apparel" | "electronics" | "pharmacy" | "services";

export interface ProductItem {
  name: string;
  price?: number | string | null;
  currency?: string;
  description?: string;
  image_url?: string;
}

export interface LocationInfo {
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
  lat?: number;
  lng?: number;
}

export interface ContactInfo {
  phone?: string;
  whatsapp?: string;
  email?: string;
  instagram?: string;
}

export interface StorefrontSpec {
  shop_name: string;
  category: StoreCategory;
  description?: string;
  products?: ProductItem[];
  hours?: string[];
  location?: LocationInfo;
  contact?: ContactInfo;
}

export interface NlpExtractRequest {
  prompt: string;
  shop_id?: string;
}

export interface NlpExtractResponse {
  storefront_spec: StorefrontSpec;
  is_valid: boolean;
  raw_prompt: string;
  invalid_fields?: string[];
}
