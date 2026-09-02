# VoiceStorefront — Cross-File / Cross-Service Flow

This traces one request end-to-end through the actual files, so any team member can
answer "what calls what" without guessing. Read with `Architect.md` (what each step does)
and `common_references.md` (the shared names used below).

## End-to-end call chain

```
[apps/web/app/(dashboard)/record/page.tsx]
        │  useRecorder() captures audio, POSTs multipart
        ▼
[services/asr-service/routers/transcribe.py]  → POST /asr/transcribe
        │  calls core/language_detect.py → core/whisper_engine.py → core/normalize.py
        ▼  returns TranscriptResult { transcript, language, confidence }
[apps/web] stores TranscriptResult in useSchemaDraft() state
        │  POSTs transcript onward
        ▼
[services/nlp-service/routers/extract.py]  → POST /nlp/extract
        │  calls core/ner_model.py → core/schema_builder.py → core/schema_validator.py
        │  (schema_validator.py may loop back into schema_builder.py up to 2x on validation failure)
        ▼  returns StorefrontSpec (packages/schemas/storefront_spec.schema.json)
[apps/web/app/(dashboard)/review/page.tsx]
        │  user reviews/edits the draft StorefrontSpec, then confirms
        ▼
[services/layout-service/routers/generate.py]  → POST /layout/generate
        │  calls core/template_classifier.py → core/palette_engine.py → core/renderer.py
        ▼  returns StorefrontBundle { html, css, js, template_id }
[services/qa-service/routers/qa.py]  → POST /qa/run
        │  calls core/sort_engine.py → core/detect_engine.py → core/repair_engine.py → core/learn_engine.py
        │  detect_engine.py and repair_engine.py may loop (detect → repair → re-detect) per violation
        ▼  returns QAReport { passed: bool, violations: [...], repairs_applied: [...] }
[services/publish-service/routers/publish.py]  → POST /publish
        │  calls core/s3_uploader.py, invalidates CloudFront
        ▼  returns { live_url, published_at }
[apps/web/app/(dashboard)/storefronts/page.tsx]
        displays the live URL + QA report to the user
```

## File-to-file dependency map

| File | Depends on (imports/calls) | Depended on by |
|---|---|---|
| `packages/schemas/storefront_spec.schema.json` | — (source of truth) | nlp-service, layout-service, apps/web/lib/api-client |
| `services/asr-service/core/whisper_engine.py` | `core/language_detect.py` output | `routers/transcribe.py` |
| `services/nlp-service/core/schema_builder.py` | `core/ner_model.py` output, `packages/schemas` | `routers/extract.py`, `core/schema_validator.py` |
| `services/layout-service/core/renderer.py` | `core/template_classifier.py`, `core/palette_engine.py`, `data/templates/*.jinja2` | `routers/generate.py` |
| `services/qa-service/core/repair_engine.py` | FAISS index (written by `core/learn_engine.py`) | `routers/qa.py` |
| `services/qa-service/core/learn_engine.py` | confirmed output of `core/detect_engine.py` re-run | FAISS index (read by `repair_engine.py` on future runs) |
| `services/publish-service/core/s3_uploader.py` | `QAReport.passed == true` gate | `routers/publish.py` |

## Two loops worth diagramming separately for the report

1. **Schema validation loop** (inside nlp-service): `schema_builder → schema_validator → (on failure) schema_builder with field-error appended`. Max 2 iterations, then hands off to human review in `review/page.tsx`.
2. **QA repair loop** (inside qa-service): `detect_engine → repair_engine → detect_engine (re-check patched section)`. Only a repair that survives re-detection is passed to `learn_engine`.

## State ownership (who is allowed to write what)

- Only `nlp-service` writes `StorefrontSpec` records.
- Only `qa-service/core/learn_engine.py` writes to the FAISS repair-rule index — no other service touches it, even for reads that could be cached elsewhere.
- Only `publish-service` writes to S3/CloudFront.

Keeping write-ownership to one service per data store is what avoids race conditions between the 4 of you working on different services in parallel.
