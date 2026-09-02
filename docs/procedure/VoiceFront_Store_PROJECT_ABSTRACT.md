# VoiceFront Store — Project Abstract & Reference

**Purpose of this file:** load this instead of re-explaining the project. It consolidates the
academic submission, the original pitch deck, and all 19 planning docs into one source. Where
docs conflict, the resolution rule is stated explicitly (see §9) — don't re-derive it.

---

## 1. Identity

| | |
|---|---|
| Title | Voicefront Store |
| Institution | Jawaharlal Nehru Trust's Smt. Indira Gandhi College of Engineering, Ghansoli 400701 |
| Program | BE Mini Project, Dept. of AI & Data Science, AY 2026–27 |
| Guide | Dr. Sunil Chavan |
| Team (4) | Siddhesh Gangurde (Leader), Dhiren Achrekar, Sarvesh Dhanrale, Aayush Tanwar |
| Timeline | 6 months, 4 people, 5 services (see §8 for track/person mapping status) |

**Open item:** the planning docs assign work to generic "Person A/B/C/D" tracks and say
"rename columns once assigned" — no doc maps a real name to a track. Don't assume a mapping;
ask if it's needed.

## 2. One-paragraph pitch

VoiceFront Store lets micro-retail shop owners with zero digital literacy create a fully
functional, mobile-optimised web storefront using only natural speech. A multilingual ASR
layer (Whisper-large-v3 + IndicXlit/IndicLID normalisation for code-mixed Hindi/Marathi) feeds
an LLM-driven intent-extraction engine that converts transcripts into a structured
`StorefrontSpec` JSON schema. A layout synthesiser fills validated, WCAG 2.2 AA templates from
that schema, and a Self-Healing QA pipeline (SORT → DETECT → REPAIR → LEARN, backed by a FAISS
repair-pattern store) autonomously detects, repairs, and learns from structural/accessibility
errors. Target: unstructured speech → published, accessible storefront in under 5 minutes, WER
< 5%, WCAG 2.2 AA > 99%, post-publish error rate < 0.5%.

## 3. Problem statement & research objectives (from the submitted framework)

Broadband exceeds 61% in Tier 2/3 Indian cities, yet fewer than 23% of India's 340M
micro-retailers run any digital storefront — the gap is an interface problem, not a
connectivity one. Existing DIY builders require coding/CMS literacy most shop owners lack.

Research objectives:
1. Multilingual ASR performance on noisy, code-mixed retail speech — domain adaptation needs.
2. Intent-extraction (NER + LLM schema-filling) for spoken description → validated schema.
3. Generative layout synthesiser under WCAG 2.2 AA + Core Web Vitals constraints.
4. Self-Healing QA pipeline (Sort→Detect→Repair→Learn) that improves with every generation.
5. Publish end-to-end in <5 min with zero human design intervention.

## 4. MVP scope

**In scope:** Hindi + English ASR (Marathi = stretch goal, not committed); 5 retail category
templates (food, apparel, electronics, pharmacy, services); 50 rule-based QA constraints (WCAG
2.2 test suite + hand-authored structural checks) + LLM-assisted repair; static hosting on S3 +
CloudFront; Next.js web frontend; WhatsApp deep-link + Google Maps embed.

**Out of scope (future work / v2.0):** real-time inventory/order processing; payment gateway
(Razorpay/UPI); self-learning QA from live production data; custom domain/SSL automation; 10+
simultaneous languages; mobile app (React Native/Expo scaffolding exists in the repo shape but
nothing inside it needs building for MVP submission); multi-tenant auth (explicit scope
decision, not an oversight — name it in the limitations section if asked).

**SDG alignment:** Primary SDG 8 (Decent Work & Economic Growth — 340M micro-retailers ≈ 22% of
India's GDP; aligns with ONDC's 30M-seller onboarding goal). Secondary SDG 10 (Reduced
Inequalities — removes literacy/technical prerequisites).

## 5. Architecture — five layers (L1–L5)

| Layer | Service | Responsibility |
|---|---|---|
| L1 | `apps/web`, `apps/mobile` | Speech acquisition: WebRTC/Expo AV capture → 16kHz mono resample → ≤30s chunks |
| L2 | `services/asr-service` | ASR & normalisation: WAV → clean transcript |
| L3 | `services/nlp-service` | Intent extraction & schema builder: transcript → validated `StorefrontSpec` |
| L4 | `services/layout-service` | Layout synthesis: `StorefrontSpec` → HTML/CSS/JS bundle |
| L5 | `services/qa-service`, `services/publish-service` | Self-healing QA + publish: bundle → live URL |

**L2 logic:** IndicLID on first 5s → language code → Whisper-large-v3 call with that language
param → normalize.py runs, in this exact order (order matters): Devanagari normalisation →
Roman→Indic transliteration (IndicXlit) → punctuation restoration (BERT). Stateless — never
persists audio; retention is an explicit opt-in S3 write, not a side effect.

**L3 logic (two-pass):** Pass 1 — IndicBERT NER (local, small, CPU-friendly) tags spans as
`SHOP_NAME, PRODUCT, PRICE, CATEGORY, HOURS, LOCATION, CONTACT, DESCRIPTION`. Pass 2 —
`schema_builder.py` calls the LLM with transcript + NER spans + JSON Schema + 3 few-shot
examples. Validation loop: JSON Schema v7 check → on failure, re-prompt with *only* the failing
field's error appended (not the whole schema — this targeted re-prompt is the basis of the
94.7% first-pass validity figure). Cap: 2 retries, then surface to human review UI.

**L4 logic:** TF-IDF + k-NN template classification (5 MVP categories — **not** the deck's
original "12 templates" claim, superseded, see §9) → colour palette lookup
(Labrecque & Milne 2012) → Jinja2 server-side render (product grid, JSON-LD hours, WhatsApp
deep-link + Maps embed). Jinja2 is logic-less by design — never let a template call back into
Python; all conditionals resolve in `renderer.py` before the template sees context. This is
also the anti-injection control (§10).

**L5 logic, four phases, always in this order:**
1. **SORT** — failure-probability model ranks sections (product grids/navbars/map embeds fail
   most historically) → 38% compute reduction by spending DETECT's budget where it matters.
2. **DETECT** — Playwright renders at 5 viewport widths (320/375/768/1024/1440); constraint
   graph checks rules (MVP: 50 rules; 400+ is the framework's target-state figure, not MVP —
   be ready to explain that gap).
3. **REPAIR** — violation embedded, matched against FAISS store (cosine sim > 0.87). Match →
   apply stored patch. No match → LLM-assisted repair generates a new patch.
4. **LEARN** — only a repair that *survives re-detection* is CodeBERT-embedded and written to
   FAISS. Failed repairs are never written back.

**What "self-healing" does NOT mean:** no LLM/NER retraining or fine-tuning from production
data in the MVP (deferred to v2.0). Learning is scoped to FAISS repair-rule accumulation —
rule accumulation, not model fine-tuning. State this precisely if a panel member probes it.

## 6. Data model essentials

- **Postgres tables:** `shops`, `audio_uploads` (metadata only — audio itself lives in S3 if
  retained), `storefront_specs` (JSONB, validated), `storefront_versions` (status enum:
  `PENDING/PROCESSING/PASSED/FAILED/REPAIRED/PUBLISHED`), `qa_reports`, `qa_violations`,
  `publications`.
- **`StorefrontSpec v1.0`** (JSON Schema draft-07, `packages/schemas/storefront_spec.schema.json`
  — the **only** place this is defined; every service imports it): required
  `shop_name, category, products, contact`. `category` enum = the 5 MVP categories. `products[]`
  need `name, price` (price = INR float). `contact.whatsapp` required, `phone` optional.
  `location` has `raw_text, lat, lng, location_verified`.
- **Redis:** qa-service only — `qa:rules:hot_cache` (FAISS mirror) and
  `qa:session:{version_id}` (TTL 10 min).
- **FAISS:** `IndexFlatIP` (cosine sim). Vectors = CodeBERT-embedded repair patches. Write path:
  only `learn_engine.py`, only after re-detection confirms the fix. Read path: only
  `repair_engine.py`, threshold hard-coded 0.87.

## 7. API contracts (all routes prefixed `/v1/...`)

| Route | Service | Notes |
|---|---|---|
| `POST /asr/transcribe` | asr-service | multipart; 422 `AsrError` on format/transcription failure |
| `POST /nlp/extract` | nlp-service | 200 even when `is_valid: false` (retries exhausted) — that's a normal outcome, not an error |
| `POST /layout/generate` | layout-service | 422 `LayoutError` on no template match / render fail |
| `POST /qa/run` | qa-service | 500 `QaViolationError` reserved for pipeline crash — violations *found* is a normal 200 |
| `POST /publish` | publish-service | server re-validates `qa_report.passed` against DB, never trusts the client; 409 `PublishError` |

Shared conventions: all timestamps ISO 8601 UTC; all IDs UUIDv4; every error body is
`{error_code, message}` parsed by one function (`parseApiError()`); pagination is
cursor-based (`?limit=&cursor=`), not offset.

## 8. Team, tracks, and timeline

**Tracks (ownership must be recorded explicitly, not assumed):**
- Track A → asr-service (L1+L2)
- Track B → nlp-service (L3)
- Track C → layout-service (L4)
- Track D → qa-service + publish-service (L5) — most cross-dependencies, heaviest load in
  Phase 4; should spend early months on constraint-rules + FAISS/Playwright scaffolding rather
  than waiting idle.

`apps/web` is shared, wired incrementally by whichever track is touching it — not a 5th job.

**Dependency chain:** D is blocked on C's real HTML output; C is blocked on B's real
`StorefrontSpec` output. If B slips, C and D both stall. Mitigate: D validates against static
seed fixtures from Month 1, not waiting for real C output.

**6-month arc:**
- **M1 — Foundations:** freeze `StorefrontSpec v1.0` (blocks everything), repo scaffold, Docker
  Compose stub stack, Groq keys for all 4, buy domain. Track A tests Marathi specifically
  (don't assume it works).
- **M2 — Vertical slice:** one full path, food category only, no QA yet. First demo.
- **M3 — QA online:** SORT+DETECT functional; schema retry loop tested; remaining 4 templates
  built. Checkpoint: QA report generated (violations detected, not yet repaired).
- **M4 — Self-healing + publish:** REPAIR+LEARN implemented; publish-service live; first
  full end-to-end run timed against <5min TTL.
- **M5 — Hardening + evaluation:** every metric in §11 measured for real against Groq; one-time
  rented-GPU (`g4dn.xlarge`) run to re-measure WER/F1 self-hosted for the Table 4 comparison;
  50-user pilot cohort starts (30-day window — the single least-flexible constraint in the
  whole timeline, start as early in M5 as possible); security pass.
- **M6 — Report, defense, pilot close-out:** compile target-vs-actual (don't hide gaps); freeze
  code; rehearse demo twice on actual defense hardware/network; pre-recorded backup video in
  case live ASR/Groq/network fails.

Non-negotiable checkpoints: end of Phase 1/2/3/4/5 (steps 43/54/64/74/84 in `procedure_plan.md`)
— don't skip under time pressure.

## 9. Superseded facts — resolve conflicts this way, don't re-litigate

The original submitted framework (pitch deck v2 + the abstract form) and the later planning
docs disagree on several points because the team pivoted mid-planning. **The planning docs
(`inference_hosting_plan.md` is the canonical trigger doc) are the current, operative plan.**
The deck reflects the *original* proposal as academically submitted — keep both facts straight,
but default to the newer plan for anything about what's actually being built:

| Topic | Deck v2 / original framework said | Current operative plan says |
|---|---|---|
| Whisper/LLM hosting | AWS EC2 + GPU instances (self-hosted) | **Groq's free hosted API**, for everything except one Month-5 validation run — this is the single biggest change, drives all the others below |
| Schema-fill / repair LLM | Llama-3-8B / Gemma-2-9B via **Ollama** | Same models family, but **Groq-hosted** (`llama-3.1-8b-instant`, or `llama-3.3-70b-versatile` for quality) |
| AWS infra | GPU-bearing EC2 | **`t3.micro`, CPU-only**, free-tier — no GPU needed anywhere except the Month-5 rental |
| Layout templates | "12 templates," k-NN classifier over 12 | **5 templates for MVP** (one per category); 12 was aspirational/target-state |
| QA rule count | "400+ rules" | **50 rules for MVP**; 400+ is the target-state figure, gap should be named to mentors explicitly |
| Team hardware relevance | N/A | Per-person GPU/VRAM analysis in `hardware.md` is **no longer the operative constraint** — kept only as context for *why* the Groq pivot happened |

If a person asks something that only the deck describes (e.g. TTFB numbers, market-opportunity
chart, monetisation path) — that content is real (§12) but belongs to the pitch/business layer,
not the technical build plan; don't let it leak into architecture answers as if it were current
engineering fact.

## 10. Security posture (MVP-scoped, not generic checklist)

- `POST /asr/transcribe` is the only endpoint accepting arbitrary binary input — highest-risk
  surface. Server-side format/duration/magic-byte checks, rejected *before* reaching Whisper (a
  bad file now burns a real Groq call against the shared team quota).
- Jinja2 autoescaping never disabled; no raw HTML from spoken content piped through `|safe`.
- Transcript → LLM prompt is untrusted input; blast radius is bounded by JSON Schema
  validation downstream (worst case = malformed field, not code execution).
- S3: public read only on the published-storefront prefix; no public write ever.
- No auth layer in MVP (explicit scope decision) → rate limiting is the main abuse control, and
  it now also protects the shared Groq free-tier quota from being exhausted by one abusive user
  or by two teammates load-testing simultaneously.
- `GROQ_API_KEY` is the most sensitive credential in the system now — AWS Secrets Manager for
  staging, never committed, rotate immediately if ever pasted anywhere it shouldn't be.

## 11. Evaluation framework — targets and how they're actually measured

| Target | Test | Note |
|---|---|---|
| WER < 5% in-domain | `test_wer.py`, 200-utterance benchmark | Groq free tier caps ~2000 req/day; cache raw results, don't re-run same day |
| Field-extraction F1 > 0.90 | `test_schema_f1.py`, 500 gold transcripts | Groq per-minute limit (~30 RPM) throttles a 500-call run — batch deliberately |
| WCAG 2.2 AA pass rate > 99% | `test_wcag_compliance.py` (axe-core) | Unaffected by the Groq pivot |
| Core Web Vitals | `test_lighthouse_ci.py` | Hard CI gate |
| Post-publish error rate < 0.5% | Client error beacon, aggregated over 30-day pilot | Production metric, not demoable in the viva |
| Avg repair latency < 800ms | `test_repair_latency.py`, FAISS-match vs LLM-generated measured separately | Original target assumed local inference — a Groq round-trip adds real network latency; report honestly if it's exceeded, don't quietly redefine the target |
| TTL < 5 min | `test_ttl_stopwatch.py` | Now includes real Groq round-trip time — more honest than a local-only number |
| NPS > 65, task completion > 90% | Usability study, not a code test | Needs its own protocol doc if rigor is required |

Explicitly NOT tested in MVP (name proactively, don't wait to be asked): load/stress testing,
fuzz testing beyond format/size validation, automated regression on FAISS repair-quality drift
over time (a real gap given the continual-learning claims — call it future work).

## 12. Business/impact framing (from the deck — pitch layer, not engineering)

- Market: 340M micro-retailers globally, ≈22% of India's GDP from this segment; <23% currently
  have any digital storefront despite >61% Tier 2/3 broadband penetration.
- Adoption targets pitched: 5,000 / 50,000 / 250,000 cumulative storefronts published across
  Year 1/2/3 — Year 3 ≈0.8% of ONDC's 30M-seller-by-2027 goal (explicitly framed as a
  conservative early wedge, not full TAM capture).
- Monetisation (post-MVP, not costed): freemium storefront + paid CDN/custom-domain tier + ONDC
  catalog-export as premium add-on. MVP itself has no payment processing.
- Positioning: Digital India + ONDC alignment, architected for future Beckn-protocol catalog
  export (aspirational, not built in MVP).

## 13. Naming conventions (the tie-breaker doc — if code disagrees with this, code is wrong)

- Python: `snake_case` funcs/vars, `PascalCase` Pydantic models. TypeScript: `camelCase`
  funcs/vars, `PascalCase` types/components. Concept name never changes across the boundary,
  only the casing.
- Every service error subclasses `VoiceStorefrontError` (`AsrError`, `SchemaValidationError`,
  `LayoutError`, `QaViolationError`, `PublishError`) — never raise a bare `Exception`.
- Env vars: `{SERVICE}_{RESOURCE}`, except `GROQ_API_KEY` (shared, no prefix, used by 3 services).
- `packages/common-utils/groq_client.py` is the **only** place any service calls Groq from.
- Status enum used everywhere, exact case: `PENDING, PROCESSING, PASSED, FAILED, REPAIRED, PUBLISHED`.

---

*This file is a synthesis of `api_contracts.md`, `Architect.md`, `common_references.md`,
`data.md`, `deployment.md`, `environment.md`, `files.md`, `flow.md`, `hardware.md`,
`inference_hosting_plan.md`, `integration.md`, `milestones.md`, `person_a–d_*.md`,
`procedure_plan.md`, `security.md`, `team_phase_plan.md`, `testing.md`, the pitch deck
(`VoiceStorefront_Deck_v2.pptx`), and the academic abstract submission form. If any source
doc is updated, this file should be regenerated rather than hand-patched piecemeal.*
