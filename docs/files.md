# VoiceStorefront — Project File & Folder Structure

Monorepo layout. Every service is independently deployable; `packages/` holds
code shared across services so naming and types never drift (see `common_references.md`).

```
voice-storefront/
├── apps/
│   ├── web/                              # Next.js 14 (App Router) — public-facing dashboard + storefront preview
│   │   ├── app/
│   │   │   ├── (dashboard)/
│   │   │   │   ├── record/page.tsx       # voice capture UI (WebRTC)
│   │   │   │   ├── review/page.tsx       # schema review / edit before publish
│   │   │   │   └── storefronts/page.tsx  # list of published storefronts
│   │   │   ├── api/                      # Next.js route handlers (thin proxies to backend)
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   ├── hooks/                        # useRecorder, useSchemaDraft, usePublishStatus
│   │   ├── lib/api-client/               # generated from packages/schemas
│   │   └── public/
│   │
│   └── mobile/                           # React Native + Expo SDK 54 (Phase 2, out of MVP scope)
│       ├── src/screens/
│       ├── src/hooks/
│       └── app.json
│
├── services/
│   ├── asr-service/                      # L2 — Whisper-large-v3 + IndicXlit + IndicLID
│   │   ├── main.py                       # FastAPI entrypoint
│   │   ├── routers/transcribe.py
│   │   ├── core/
│   │   │   ├── whisper_engine.py
│   │   │   ├── language_detect.py        # IndicLID wrapper
│   │   │   ├── normalize.py              # Devanagari + transliteration + punctuation
│   │   │   └── validation.py             # magic-byte/format/size checks — runs before whisper_engine.py, see security.md
│   │   ├── models/                       # Pydantic request/response models
│   │   └── tests/
│   │       ├── unit/                     # mocked whisper/IndicLID calls
│   │       └── integration/
│   │           └── test_wer.py           # 200-utterance WER benchmark, see testing.md
│   │
│   ├── nlp-service/                      # L3 — NER + LLM schema builder
│   │   ├── main.py
│   │   ├── routers/extract.py
│   │   ├── core/
│   │   │   ├── ner_model.py              # IndicBERT fine-tuned
│   │   │   ├── schema_builder.py          # LLM prompt orchestration (Llama-3 / Gemma-2)
│   │   │   └── schema_validator.py        # JSON Schema v7 validation + re-prompt loop
│   │   ├── prompts/                      # few-shot templates
│   │   └── tests/
│   │       ├── unit/
│   │       └── integration/
│   │           └── test_schema_f1.py     # 500-transcript gold F1 benchmark, see testing.md
│   │
│   ├── layout-service/                   # L4 — template selection + rendering
│   │   ├── main.py
│   │   ├── routers/generate.py
│   │   ├── core/
│   │   │   ├── template_classifier.py    # TF-IDF + k-NN category selection
│   │   │   ├── renderer.py               # Jinja2 rendering
│   │   │   └── palette_engine.py         # colour-psychology palette mapping
│   │   ├── templates/                    # 5 category Jinja2 templates (MVP)
│   │   └── tests/
│   │
│   ├── qa-service/                       # L5 — Self-Healing QA
│   │   ├── main.py
│   │   ├── routers/qa.py
│   │   ├── core/
│   │   │   ├── sort_engine.py            # failure-probability ranking
│   │   │   ├── detect_engine.py          # Playwright + constraint graph
│   │   │   ├── repair_engine.py          # FAISS lookup + LLM-assisted repair
│   │   │   └── learn_engine.py           # CodeBERT embedding + FAISS write
│   │   ├── rules/                        # WCAG 2.2 + structural constraint definitions
│   │   └── tests/
│   │       ├── unit/
│   │       └── integration/
│   │           └── test_repair_latency.py  # FAISS-match vs LLM-generated timing, see testing.md
│   │
│   └── publish-service/                  # deploy to S3 + CloudFront, issue live URL
│       ├── main.py
│       ├── routers/publish.py
│       ├── core/s3_uploader.py
│       └── tests/
│
├── packages/                             # shared across every service — single source of truth
│   ├── schemas/                          # StorefrontSpec v1.0 JSON Schema + generated types (py + ts)
│   ├── common-utils/                     # logging, config loader, custom exceptions, retry/backoff
│   └── api-client/                       # typed client consumed by apps/web
│
├── infra/
│   ├── docker/
│   │   └── docker-compose.dev.yml        # one Dockerfile per service (in each service's own folder) + this compose file
│   ├── terraform/                        # AWS EC2 (per Table 4 — not ECS, see deployment.md), S3, CloudFront, RDS, ElastiCache
│   │   ├── main.tf                       # provider config, backend state (S3 + DynamoDB lock)
│   │   ├── networking.tf                 # VPC, subnets, security groups
│   │   ├── ec2.tf                        # instance definitions, security groups, systemd provisioning
│   │   ├── rds.tf
│   │   ├── elasticache.tf
│   │   ├── s3_cloudfront.tf              # storefront hosting + app CDN
│   │   └── variables.tf                  # includes documented EC2 service-grouping decision, see deployment.md
│   └── ci-cd/                            # GitHub Actions workflows — build → push to ECR → deploy via SSM to EC2
│
├── data/
│   ├── templates/                        # raw HTML/CSS source for the 5 MVP category templates
│   ├── constraint-rules/                 # 50 pre-defined QA rules (JSON)
│   └── seed/
│       ├── storefront_specs/             # sample StorefrontSpec fixtures for testing
│       └── asr_benchmark/                # 200-utterance gold-transcript set, see testing.md
│
├── docs/
│   ├── files.md
│   ├── Architect.md
│   ├── flow.md
│   ├── common_references.md
│   ├── integration.md
│   ├── data.md
│   ├── api_contracts.md
│   ├── environment.md
│   ├── testing.md
│   ├── deployment.md
│   ├── security.md
│   └── milestones.md
│
└── tests/
    └── e2e/                              # Playwright end-to-end: voice-in → live-URL-out
        ├── test_wcag_compliance.py       # axe-core across templates × viewports
        ├── test_lighthouse_ci.py         # Core Web Vitals CI gate
        └── test_ttl_stopwatch.py         # <5 min time-to-live timer
```

## Notes on this structure
- Each `services/*` folder is a standalone FastAPI app — deployable and scalable independently, matching the five-layer architecture in the theoretical framework (L1–L5).
- `packages/schemas` is the **only** place `StorefrontSpec` is defined. Every service imports from it — never redefine the schema locally. This is what prevents the four of you from drifting into four different field names for the same concept.
- `apps/mobile` exists now so the repo shape doesn't change in Phase 2, but nothing inside it needs building for the MVP submission.
- **Infra decision, recorded here to avoid drift:** deployment target is EC2, matching Table 4 of the submitted framework — not ECS. `deployment.md` has the full rationale and instance-grouping recommendation. If the team later wants to revisit this, it's a mentor conversation, not a silent Terraform change.
- `tests/` subfolders (`unit/`, `integration/`) and the specific benchmark files above map directly to the evaluation-framework targets in `testing.md` — that file is the canonical explanation of *why* each test exists, this file just tracks *where* it lives.
