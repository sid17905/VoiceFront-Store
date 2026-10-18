# 01 — Project Audit (Read-Only, Evidence-Based)

**Project:** VoiceFront Store — BE Mini Project, Dept. of AI & Data Science,
Jawaharlal Nehru Trust's Smt. Indira Gandhi College of Engineering, Ghansoli (AY 2026–27).
**Guide:** Dr. Sunil Chavan. **Team (4):** Siddhesh Gangurde (Leader), Dhiren Achrekar,
Sarvesh Dhanrale, Aayush Tanwar.
**Audit date:** 2026-10-11. **Audit type:** read-only inspection of docs, source, git state.
**No source files were modified.**

> Scope note: this is a status/evidence audit only. The implementation roadmap is in
> `03_UPDATED_WORKING_PLAN.md`; the scope decision is in `07_FIVE_PHASE_SCOPE_AND_PRESENTATION_PLAN.md`.

---

## 1. One-line summary

The project has pivoted (documented in `docs/v2/v2_architecture_and_implementation_plan.md`)
to a **Prompt-First English Baseline**: the backend text→storefront pipeline
(NLP → Layout → QA) is substantially implemented and demoable, while **multilingual voice
(ASR/IndicLID/IndicXlit/IndicBERT)** is deliberately **stubbed to English and deferred**. The
Flutter mobile app is a polished UI but currently runs on **mock data, not wired to the live
backend** — this is the single biggest gap for a credible end-to-end demo.

---

## 2. What the project is (from the docs)

- **Goal:** micro-retail shop owners create a mobile web storefront from natural language.
- **Original 5-layer architecture** (`VoiceFront_Store_PROJECT_ABSTRACT.md` §5):
  - L1 speech acquisition → L2 ASR → L3 NLP intent/schema → L4 layout synthesis →
    L5 self-healing QA + publish.
- **Operative pivot (v2):** input is an **English text prompt** (voice optional/deferred);
  everything downstream is unchanged. `inference_hosting_plan.md` is the canonical trigger doc:
  all LLM/ASR runs on **Groq's hosted API**, not local GPUs.

---

## 3. Repository map (what actually exists on disk)

| Area | Path | Exists | Notes |
|---|---|---|---|
| ASR service | `services/asr-service/` | ✅ | Groq Whisper call + simulated fallback; lang stubbed to EN |
| NLP service | `services/nlp-service/` | ✅ | **Real working core** — Groq Llama-3.3-70b + regex fallback |
| Layout service | `services/layout-service/` | ✅ | **Working** Jinja2 render, 5 templates, palettes, scrape+component lib |
| QA service | `services/qa-service/` | ✅ | DETECT done; SORT/REPAIR/LEARN stubbed |
| Publish service | `services/publish-service/` | ✅ | Exists; S3 mocked; v2 wants it folded into qa (not yet done) |
| Shared schemas | `packages/schemas/` | ✅ | Pydantic (`entity_types.py`) + JSON Schema + TS — single source of truth |
| API client (TS) | `packages/api-client/index.ts` | ✅ | nlp/layout/qa methods (no asr/publish) |
| Shared utils | `packages/common_utils/` (underscore) | ✅ | Operative; `common-utils` (hyphen) is the broken-import copy |
| Flutter app | `voicefront/` | ✅ | 5 screens, polished UI, **mock data** (not wired to backend) |
| Next.js web | `apps/web/` | ✅ (older) | Original dashboard from the docs; not the current demo frontend |
| Mobile stub | `apps/mobile/` | ✅ (stub) | `app.json` only |
| Docker | `infra/docker/docker-compose.dev.yml` | ✅ | 4 services wired (asr/nlp/layout/qa), ports 8001–8004 |
| Component library | `data/component-library/` | ✅ | food fully covered; others partial → fall back to monolith |
| QA fixtures | `data/seed/rendered_bundles/fixture-{good,bad}.html` | ✅ | DETECT can be exercised |
| E2E test | `tests/e2e/test_prompt_pipeline.py` | ✅ | prompt→spec→HTML, passes without a Groq key |
| Scrapling tool | `tools/scrape_with_scrapling.py`, `layout-service/_playwright_worker.py` | ✅ | v2 scraping direction |
| Visualizer | `docs/procedure/pipeline-visualizer.html`, `docs/pipeline-visualizer.html` | ✅ | live DOM demo artifact |
| Papers | `docs/papers/` (20 refs) | ✅ | literature review source |
| **Stray/unrelated** | `docs/HACKERHOUSE _NEXT.txt` | ⚠️ | A DIFFERENT project ("TraceFace" biometric OSINT) — ignore |
| README | `README.md` | ⚠️ | **empty** |

---

## 4. Per-service implementation status (evidence)

### 4.1 asr-service — Phase 1 (Voice input) · PARTIAL, English-stubbed
- `main.py` FastAPI on `:8001`; `routers/transcribe.py` wired validation → language_detect → whisper_engine.
- `core/whisper_engine.py`: **real** Groq `whisper-large-v3` call if `GROQ_API_KEY` is set;
  otherwise returns a **simulated transcript** ("Tony's Pizza Kitchen…"). `language="en"` default.
- `core/language_detect.py`: **stub** — `return default` ("en") with docstring
  *"In V2 English baseline, defaults strictly to English. Provides pluggable interface for future
  IndicLID integrations."* → multilingual detection deliberately deferred.
- `core/normalize.py`: light regex cleanup (whitespace, currency "Rs", phone) — no Devanagari /
  IndicXlit / BERT punctuation (the abstract's L2 pipeline is **not** implemented).
- `requirements.txt`: `fastapi, uvicorn, pydantic, python-multipart, httpx, groq` — **no torch/transformers**.
- **Verdict:** boots and returns a valid response shape; real transcription needs a key; multilingual stack absent by design.

### 4.2 nlp-service — Phase 2 (Understanding) · WORKING (demo core)
- `core/schema_builder.py`: **real** 2-attempt Groq Llama-3.3-70b extraction with a strict JSON system
  prompt and a validation-error re-prompt loop; **plus** `_heuristic_fallback_extractor()` (regex) so it
  **works with no key and no network**.
- `core/schema_validator.py`: Pydantic validation against `StorefrontSpec`, returns `(spec, is_valid, errors)`.
- `routers/extract.py`: `POST /v1/nlp/extract`, accepts **`prompt` OR `transcript`** → `NlpExtractResponse`.
- `core/ner_model.py`: regex-only compatibility shim (phone/price); **not IndicBERT**, and **not used** in
  the extract path. IndicBERT NER deferred (consistent with v2).
- **Verdict:** the strongest, most demoable component; resilient offline.

### 4.3 layout-service — Phase 3 (Page building) · WORKING
- `main.py` on `:8003`; routers `generate` + `scrape`.
- `routers/generate.py`: `POST /v1/layout/generate` wires `select_template → get_palette → render`.
- `core/template_classifier.py`: **stub** — returns `spec["category"]` directly (TF-IDF k-NN deferred to a
  later phase; fine because category is schema-validated upstream).
- `core/renderer.py`: Jinja2 with **autoescaping ON**; two paths — component-library assembly (used only
  when all 4 section types have APPROVED variants) else monolithic template. Emits JSON-LD, WhatsApp `wa.me/`
  link, responsive CSS. All **5 templates present** (`food/apparel/electronics/pharmacy/services.jinja2`).
- `core/palette_engine.py`: 5 category palettes (Labrecque & Milne 2012).
- `core/component_picker.py` + `routers/scrape.py` + `_playwright_worker.py`: v2 component-library + live
  scraping direction (depends on Playwright/Scrapling at runtime).
- **Verdict:** renders all 5 categories; component-assembly path strongest for `food`.

### 4.4 qa-service — Phase 4 (Quality) · PARTIAL (DETECT only)
- `routers/qa.py`: `POST /v1/qa/run` wires `load_rules → rank_failure_risk (pass-through) → detect_violations`;
  resolves bundles against **seed fixtures** (`data/seed/rendered_bundles/{version_id}.html`).
- `core/detect_engine.py`: **real** multi-viewport (320/375/768/1024/1440) axe-core + custom checks via
  **Playwright** — but Playwright/axe-core could not be run in the author's sandbox (see `PERSON_D_README.md`);
  must be verified on team hardware.
- `core/sort_engine.py`, `repair_engine.py`, `learn_engine.py`: **documented pass-through stubs** (FAISS/CodeBERT
  self-healing is Phase-later work). `passed` is True only when zero violations — expected at this stage.
- **Verdict:** DETECT is code-complete and unit-tested with a fake page; needs real-browser verification. No repair/learn.

### 4.5 publish-service — Phase 5 (Go-live) · GROUNDWORK ONLY
- `core/s3_uploader.py` + `routers/publish.py` exist; S3/boto3 **mocked**, no live AWS; server-side
  `qa_report.passed` re-check stubbed to `True`. v2 intends to **consolidate this into qa-service** (not done).
- **Verdict:** weakest end-to-end link; a real published live URL is not currently demonstrable.

---

## 5. Frontend status

- **Flutter `voicefront/`** (the demo frontend per `docs/start-demo-sep.txt`): 5 screens
  (home / record / review-edit / preview-QA / storefronts) + settings placeholder.
  - `screens/record_screen.dart`: EN/HI language toggle and a **simulated** transcript stream
    (`_startSimulatedStream` types a hardcoded sample word-by-word). **No real microphone capture.**
  - `services/groq_api_service.dart`: has a Whisper call but the key is the placeholder
    `gsk_YOUR_GROQ_API_KEY_HERE`, so it returns **hardcoded** EN/HI transcripts; **not invoked** by the record flow.
  - `screens/review_edit_screen.dart` + `data/static_data.dart`: **all values hardcoded** ("Krishna Sweets",
    "94.7% Conf.", published storefronts). **No HTTP calls to nlp/layout/qa.**
  - **Verdict:** excellent UX prototype, but **not integrated** with the backend. Wiring it is the main demo task.
- **Next.js `apps/web/`**: the original dashboard the planning docs describe (`record/review/storefronts`
  pages). Present but not the current demo path.

---

## 6. Integration & environment

- `docker-compose.dev.yml`: builds asr(8001)/nlp(8002)/layout(8003)/qa(8004) from `python:3.12-slim`
  Dockerfiles; mounts `packages/` and `data/`. publish-service **not** in compose.
- `pytest.ini` at root: `pythonpath = . packages`, `asyncio_mode = auto`.
- `packages/api-client/index.ts`: `VoiceFrontClient` points at `localhost:8001-8004`; exposes
  `extractMetadata`, `generateLayout`, `runQa` — **no** `transcribe`/`publish` (matches the pivot).
- Groq is called **directly** inside `whisper_engine.py` and `schema_builder.py`. The naming doc's
  "single `groq_client.py` wrapper" **does not exist** — minor architectural drift.

---

## 7. Tests present

| Test | Path | What it checks | Runnable in audit? |
|---|---|---|---|
| E2E prompt pipeline | `tests/e2e/test_prompt_pipeline.py` | prompt→spec(food)→HTML (shop name, wa.me, viewport) | ✅ (no key needed) |
| Layout all categories | `services/layout-service/tests/test_all_categories.py` | 5 categories render w/ JSON-LD + wa.me | ✅ likely |
| Layout render/components | `services/layout-service/tests/test_{render,components,layout_service}.py` | render paths | ✅ likely |
| NLP schema F1 | `services/nlp-service/tests/integration/test_schema_f1.py` | extraction accuracy | needs key/data |
| ASR WER | `services/asr-service/tests/integration/test_wer.py` | WER benchmark | needs key/data |
| QA detect/rules/stubs | `services/qa-service/tests/...` | detect mapping w/ fake page | partial (no real browser) |

> Tests were **not executed** during this audit (planning-only; avoids installing packages / downloading
> browsers/models). Status above is from reading the test bodies. Running them is a Week-11/12 verification task.
>
> **Deep-read note:** the documented evaluation suite (`test_wcag_compliance.py`, `test_lighthouse_ci.py`,
> `test_ttl_stopwatch.py`, and the WER/F1 benchmarks named in `testing.md`) is **not present** in the repo —
> only `test_prompt_pipeline.py` exists. The WER/F1/WCAG/CWV/TTL targets are therefore currently unmeasured.

---

## 8. Multilingual-voice status (the deferred feature)

- **Architecturally present, functionally English-only.** `language_detect.py` returns `"en"`; `normalize.py`
  has no Indic transliteration/punctuation; `ner_model.py` is regex, not IndicBERT; the nlp system prompt says
  *"English text prompts or spoken transcripts."* Hindi UI strings and a Hindi sample exist in the Flutter app,
  and the LLM path can technically process Hindi text, but **no validated multilingual voice pipeline exists.**
- This **matches the required scope**: keep English-prompt scope, keep the plug-in interfaces, defer multilingual
  voice to the next presentation. Nothing multilingual needs to be removed.

---

## 9. Discrepancies & risks (flagged, not fixed)

1. **"Phase" is overloaded** across docs (Phase 0–6 timeline vs L1–L5 layers vs v2's 5-step execution path).
   The five-phase mapping used in these planning docs is defined and flagged for confirmation in `07_...`.
2. **Flutter app is on mock data** — biggest risk to a believable live demo. (Decision needed on demo path.)
3. **No real published live URL** (publish-service mocked, no AWS). Phase 5 is demonstrable only as "would publish".
4. **Playwright/axe-core unverified** on real hardware (QA DETECT). Must be run on a team laptop before the demo.
5. **`common-utils` vs `common_utils`** duplication + missing shared `groq_client.py` — tidy-up, not a blocker.
6. **v2 doc vs reality drift:** Alpine images (doc) vs `python:3.12-slim` (reality); `storefront_spec_v2.py`
   (doc) vs `entity_types.py` (reality, SSOT). Harmless but worth noting so the report is accurate.
7. **Empty `README.md`** and a **stray unrelated file** (`HACKERHOUSE _NEXT.txt`).
8. **Team→track name mapping is unrecorded** (abstract §1 explicitly says "don't assume a mapping; ask").

### Added after full-documentation deep-read (2026-10-11)
9. **StorefrontSpec contract drift (significant).** The *frozen* `StorefrontSpec v1.0` in `data.md`
   requires `shop_name, category, products, contact` — with `products[].price` a required **number**,
   `contact.whatsapp` required, `hours` as `iso8601-interval`, and `location.raw_text/lat/lng/location_verified`.
   The **operative** schema (`packages/schemas/storefront_spec.schema.json` + `entity_types.py`) requires only
   `shop_name, category`; products/contact are optional; `price` is `number|string|null`; `location` uses
   `address/city/state/pincode`. The "do-not-modify-without-team-discussion" contract was effectively changed —
   sensible for prompt-first leniency, but it should be **ratified as v1.1** (decision D7 in `07_`).
10. **API-contract drift** (`api_contracts.md` vs code): `/v1/nlp/extract` documented req `{transcript, language}`
    + resp `{…, entities, retry_count}` → code accepts `prompt|transcript`, resp `{storefront_spec, is_valid,
    raw_prompt, invalid_fields}`. `/v1/layout/generate` documented resp `{template_id, html_s3_key, version_id}`
    → code returns inline `{template_id, html}` (no S3 key / version_id). Matters when wiring the app / `api-client`.
11. **Persistence layer is design-only.** `data.md` specs 7 Postgres tables + Redis; **none are implemented** —
    no Postgres/Redis in the operative compose, `qa/run` resolves bundles from seed fixtures, publish pass-check
    stubbed. The status enum (`PENDING…PUBLISHED`) and version tracking exist only on paper. Demo runs stateless.
12. **Documented evaluation test-suite largely absent.** `testing.md`/`files.md` name `test_wcag_compliance.py`,
    `test_lighthouse_ci.py`, `test_ttl_stopwatch.py` (+ WER/F1 benchmarks). Only `tests/e2e/test_prompt_pipeline.py`
    exists → WER/F1/WCAG/CWV/TTL targets are currently **unmeasured** (no "actual" column yet for the report).
13. **`groq_client.py` is mandated by two canonical docs** (`common_references.md`, `files.md`: "the only place
    any service calls Groq from") but **does not exist** — asr/nlp each roll their own client. Convention
    violation, low risk.
14. **Flutter `voicefront/` is an undocumented new frontend.** `files.md`/`flow.md` only know `apps/web` (Next.js)
    + `apps/mobile` (stub, "out of MVP scope"). The actual demo app appears in **no** procedure doc — so plan/doc
    references to `apps/web` won't match the thing being demoed.
15. **Templates path mismatch.** Docs set `LAYOUT_TEMPLATE_DIR=./data/templates`; code defaults to
    `services/layout-service/templates/` (where the 5 `.jinja2` files actually live). Setting the documented env
    value would break rendering.
16. **Reference paper `docs/papers/18.pdf` — now identified (D8 resolved):** Othman, Dhouib & Al Jabor,
    *"Fostering websites accessibility: a case study on the use of the Large Language Models ChatGPT for
    automatic remediation"* (Mada Qatar Assistive Technology Center) — LLM-based automatic WCAG 2.1
    remediation vs manual (WAVE) testing. Directly supports the Phase-4 self-healing-QA / LLM-assisted-repair novelty.

---

## 10. Bottom line for the presentation

A reliable demo is **achievable** on the English prompt-first path with low new-code effort:
**prompt → NLP extract → layout render → QA detect**, shown in a browser (and optionally through a
wired Flutter screen). The work is mostly **integration + verification**, not new feature building.
Multilingual voice and real publishing stay **explicitly deferred**. Full plan: `03_...`; scope: `07_...`.
