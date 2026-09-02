# VoiceStorefront — Data Model

Covers PostgreSQL schema, Redis usage, FAISS index structure, and the `StorefrontSpec` JSON Schema.

## 1. PostgreSQL schema

```sql
-- One row per shop owner's project (MVP: single-tenant, no auth, but keep the table anyway)
CREATE TABLE shops (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_name       TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Raw audio metadata (not the audio itself — that lives in S3 if retained at all)
CREATE TABLE audio_uploads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID REFERENCES shops(id),
    s3_key          TEXT,
    language        TEXT,
    duration_sec    NUMERIC,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The validated StorefrontSpec produced by nlp-service
CREATE TABLE storefront_specs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id         UUID REFERENCES shops(id),
    audio_upload_id UUID REFERENCES audio_uploads(id),
    spec_json       JSONB NOT NULL,          -- validated against StorefrontSpec v1.0
    is_valid        BOOLEAN NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Each generated layout attempt (a spec can be re-rendered, e.g. after edits)
CREATE TABLE storefront_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    spec_id         UUID REFERENCES storefront_specs(id),
    template_id     TEXT NOT NULL,
    html_s3_key     TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN
                      ('PENDING','PROCESSING','PASSED','FAILED','REPAIRED','PUBLISHED')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row per QA run against a storefront_version
CREATE TABLE qa_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id          UUID REFERENCES storefront_versions(id),
    passed              BOOLEAN NOT NULL,
    total_violations     INTEGER NOT NULL DEFAULT 0,
    repaired_count       INTEGER NOT NULL DEFAULT 0,
    avg_repair_latency_ms NUMERIC,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Individual violations found within a QA report
CREATE TABLE qa_violations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id       UUID REFERENCES qa_reports(id),
    rule_id         TEXT NOT NULL,           -- matches data/constraint-rules/*.json
    viewport_width  INTEGER,
    severity        TEXT NOT NULL CHECK (severity IN ('critical','major','minor')),
    was_repaired    BOOLEAN NOT NULL DEFAULT false,
    repair_source   TEXT CHECK (repair_source IN ('faiss_match','llm_generated', NULL))
);

-- Final publish record
CREATE TABLE publications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID REFERENCES storefront_versions(id),
    live_url        TEXT NOT NULL,
    published_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 2. `StorefrontSpec v1.0` — JSON Schema (packages/schemas/storefront_spec.schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StorefrontSpec",
  "version": "1.0",
  "type": "object",
  "required": ["shop_name", "category", "products", "contact"],
  "properties": {
    "shop_name":   { "type": "string" },
    "category":    { "type": "string", "enum": ["food","apparel","electronics","pharmacy","services"] },
    "description": { "type": "string" },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "price"],
        "properties": {
          "name":  { "type": "string" },
          "price": { "type": "number", "description": "INR, normalized to float" },
          "description": { "type": "string" }
        }
      }
    },
    "hours": {
      "type": "array",
      "items": { "type": "string", "format": "iso8601-interval" }
    },
    "location": {
      "type": "object",
      "properties": {
        "raw_text":         { "type": "string" },
        "lat":              { "type": "number" },
        "lng":              { "type": "number" },
        "location_verified": { "type": "boolean" }
      }
    },
    "contact": {
      "type": "object",
      "required": ["whatsapp"],
      "properties": {
        "whatsapp": { "type": "string" },
        "phone":    { "type": "string" }
      }
    }
  }
}
```

## 3. Redis usage (qa-service only, per `integration.md`)
```
qa:rules:hot_cache          → hash of rule_id → repair pattern (mirrors FAISS index for fast lookup)
qa:session:{version_id}     → transient state during a QA run (TTL: 10 min)
```

## 4. FAISS index structure
- **Index type:** `IndexFlatIP` (inner product / cosine similarity, per Table 4).
- **Vector source:** repair patches embedded via CodeBERT.
- **Metadata stored alongside each vector:** `rule_id`, `violation_type`, `patch_diff`, `times_reused`, `created_at`.
- **Write path:** only `qa-service/core/learn_engine.py`, and only after a repair survives re-detection (see `flow.md`, loop 2).
- **Read path:** only `qa-service/core/repair_engine.py`, similarity threshold hard-coded at 0.87 per the framework.

## 5. Constraint rules file format (`data/constraint-rules/*.json`)
```json
{
  "rule_id": "wcag-2.2-aa-contrast-001",
  "category": "accessibility",
  "wcag_ref": "1.4.3",
  "check": "contrast_ratio",
  "threshold": 4.5,
  "severity": "critical"
}
```
50 such rules for MVP, sourced from the WCAG 2.2 test suite plus a smaller set of structural/rendering checks you'll need to author yourselves (viewport overflow, broken image src, missing alt text, etc. — the framework's 400+ rule figure is the target-state number, not the MVP number; be ready to explain that gap to your mentors).
