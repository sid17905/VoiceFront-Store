# VoiceStorefront — Common References & Naming Conventions

Four people, five services, two frontends. The single biggest source of avoidable bugs
in a project like this is the same concept getting three different names in three files.
This document is the tie-breaker — if code disagrees with this file, the code is wrong.

## Rule
Python services use `snake_case` for functions/variables, `PascalCase` for Pydantic models.
TypeScript/React uses `camelCase` for functions/variables, `PascalCase` for types/components.
The **concept name never changes** across the boundary — only the casing convention does.

| Concept | Python (services) | TypeScript (apps/web) | JSON field (wire format) |
|---|---|---|---|
| Transcribe audio | `transcribe_audio()` | `transcribeAudio()` | — |
| Detect language | `detect_language()` | `detectLanguage()` | `language` |
| Normalize transcript | `normalize_transcript()` | — | `transcript` |
| Extract entities (NER) | `extract_entities()` | — | `entities` |
| Build schema | `build_schema()` | — | — |
| Validate schema | `validate_schema()` | `validateSchemaDraft()` | `is_valid` |
| The core data object | `StorefrontSpec` (Pydantic) | `StorefrontSpec` (TS type) | `storefront_spec` |
| Select template | `select_template()` | — | `template_id` |
| Render storefront | `render_storefront()` | — | — |
| Generated bundle | `StorefrontBundle` | `StorefrontBundle` | `storefront_bundle` |
| Run QA pipeline | `run_qa_pipeline()` | `triggerQaRun()` | — |
| Rank failure risk | `rank_failure_risk()` | — | `risk_score` |
| Detect violations | `detect_violations()` | — | `violations` |
| Repair a violation | `repair_violation()` | — | `repairs_applied` |
| Vectorize + store a rule | `vectorize_rule()` | — | — |
| QA outcome object | `QAReport` (Pydantic) | `QaReport` (TS type) | `qa_report` |
| Publish storefront | `publish_storefront()` | `publishStorefront()` | — |
| Live URL result | `PublishResult` | `PublishResult` | `live_url` |
| Call Groq (shared wrapper) | `call_groq_whisper()` / `call_groq_chat()` in `packages/common-utils/groq_client.py` | — | — |

## Entity type constants (used identically in NER, schema, and frontend form labels)
```
SHOP_NAME, PRODUCT, PRICE, CATEGORY, HOURS, LOCATION, CONTACT, DESCRIPTION
```
Defined once in `packages/schemas/entity_types.py` (and mirrored as a TS enum in
`packages/schemas/entity_types.ts`, generated — never hand-edited).

## HTTP endpoint naming pattern
`POST /{domain}/{verb}` — domain matches the service, verb matches the function above minus the `_` suffix:
- `POST /asr/transcribe`
- `POST /nlp/extract`
- `POST /layout/generate`
- `POST /qa/run`
- `POST /publish`

## Error naming convention
Every service raises from a shared base in `packages/common-utils/exceptions.py`:
`VoiceStorefrontError` → subclassed as `AsrError`, `SchemaValidationError`, `LayoutError`, `QaViolationError`, `PublishError`. Never raise a bare `Exception` — the API gateway maps these subclasses to HTTP status codes, so an unmapped exception becomes an opaque 500 the frontend can't display meaningfully.

## Status/enum values (must match exactly, including case, across every service)
```
PENDING, PROCESSING, PASSED, FAILED, REPAIRED, PUBLISHED
```

## Environment variable naming
`{SERVICE}_{RESOURCE}` — e.g. `ASR_GROQ_MODEL`, `NLP_GROQ_MODEL`, `QA_FAISS_INDEX_PATH`, `PUBLISH_S3_BUCKET`, and the shared `GROQ_API_KEY` (no service prefix — it's used by three services). Full list is in `environment.md`.
