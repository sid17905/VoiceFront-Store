# VoiceStorefront — API Contracts

Versioned request/response shapes for every endpoint named in `flow.md`. Naming follows
`common_references.md` exactly — `snake_case` JSON fields, enum values in `UPPER_CASE`.
Treat this file as the schema source for hand-written contracts; `packages/schemas` is the
machine-readable mirror generated from these (or vice versa — pick one direction and don't
let them diverge; recommendation: hand-edit here, generate JSON Schema + Pydantic + TS from it).

API version prefix: `/v1/...` on every route below (omitted in `flow.md` for brevity).

---

## POST /v1/asr/transcribe
**Service:** asr-service

Request (`multipart/form-data`):
```json
{
  "audio_file": "<binary, wav/mp3/ogg>",
  "shop_id": "uuid (optional — omit for first-time capture)"
}
```

Response `200`:
```json
{
  "transcript": "string",
  "language": "hi | en | mr",
  "confidence": 0.0,
  "segments": [
    { "start_sec": 0.0, "end_sec": 4.2, "text": "string" }
  ]
}
```

Error `422 AsrError`:
```json
{ "error_code": "ASR_UNSUPPORTED_FORMAT | ASR_TRANSCRIPTION_FAILED", "message": "string" }
```

---

## POST /v1/nlp/extract
**Service:** nlp-service

Request:
```json
{
  "transcript": "string",
  "language": "hi | en | mr",
  "shop_id": "uuid (optional)"
}
```

Response `200`:
```json
{
  "storefront_spec": { "$ref": "StorefrontSpec v1.0 — see data.md" },
  "is_valid": true,
  "entities": [
    { "type": "SHOP_NAME | PRODUCT | PRICE | CATEGORY | HOURS | LOCATION | CONTACT | DESCRIPTION",
      "value": "string", "confidence": 0.0 }
  ],
  "retry_count": 0
}
```

Response `200` (validation exhausted retries — per the 2-retry cap in `Architect.md`):
```json
{
  "storefront_spec": { "...partial, best-effort..." },
  "is_valid": false,
  "invalid_fields": [ { "field": "contact.whatsapp", "reason": "string" } ]
}
```

Error `422 SchemaValidationError` — only for malformed input, not for a schema that failed validation (that's a `200` with `is_valid: false`, since it's a normal, expected outcome the UI handles).

---

## POST /v1/layout/generate
**Service:** layout-service

Request:
```json
{ "storefront_spec": { "$ref": "StorefrontSpec v1.0" } }
```

Response `200`:
```json
{
  "storefront_bundle": {
    "template_id": "food | apparel | electronics | pharmacy | services",
    "html_s3_key": "string",
    "version_id": "uuid"
  }
}
```

Error `422 LayoutError`:
```json
{ "error_code": "LAYOUT_NO_TEMPLATE_MATCH | LAYOUT_RENDER_FAILED", "message": "string" }
```

---

## POST /v1/qa/run
**Service:** qa-service

Request:
```json
{ "version_id": "uuid" }
```

Response `200`:
```json
{
  "qa_report": {
    "passed": true,
    "total_violations": 3,
    "repaired_count": 3,
    "avg_repair_latency_ms": 410,
    "violations": [
      {
        "rule_id": "wcag-2.2-aa-contrast-001",
        "severity": "critical | major | minor",
        "viewport_width": 375,
        "was_repaired": true,
        "repair_source": "faiss_match | llm_generated"
      }
    ]
  },
  "status": "PASSED | FAILED | REPAIRED"
}
```

Error `500 QaViolationError` — reserved for pipeline failure (Playwright crash, FAISS unreachable), never for "violations found" — violations found is a normal `200`.

---

## POST /v1/publish
**Service:** publish-service

Request:
```json
{ "version_id": "uuid" }
```

Precondition: caller must have already received `qa_report.passed == true` — publish-service re-validates this server-side against `qa_reports` table rather than trusting the client.

Response `200`:
```json
{ "live_url": "https://cdn.voicestorefront.app/{slug}", "published_at": "ISO 8601 timestamp" }
```

Error `409 PublishError`:
```json
{ "error_code": "PUBLISH_QA_NOT_PASSED | PUBLISH_S3_FAILED", "message": "string" }
```

---

## Cross-cutting conventions for every endpoint
- All timestamps: ISO 8601, UTC.
- All IDs: UUIDv4.
- All error bodies share the shape `{ "error_code": "string", "message": "string" }` — the frontend has exactly one error-parsing function (`parseApiError()` in `packages/api-client`), not one per service.
- Pagination (only relevant to `storefronts/page.tsx` listing published sites): `?limit=&cursor=`, not offset-based.
