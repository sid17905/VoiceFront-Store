# 07 — Five-Phase Scope & Presentation Plan (MASTER)

**Project:** VoiceFront Store · **Date:** 2026-10-11 · **Mode:** planning only (no code written).
This is the master scope document. Companion files: `01_PROJECT_AUDIT.md` (evidence),
`02_DOCS_COMPARISON_PREVIOUS_VS_LATEST.md`, `03_UPDATED_WORKING_PLAN.md` (execution),
`04_MAJOR_PROJECT_DIARY_WEEKS_07-12.md` (diary drafts).

---

## 0. IMPORTANT — on "the five phases" (ambiguity flagged for your confirmation)

The word **"phase"** is used three different ways in the project's own documents:

- **Timeline phases 0–6** (`procedure_plan.md`, `team_phase_plan.md`, `milestones.md`) — 6-month calendar.
- **Architecture layers L1–L5** (`VoiceFront_Store_PROJECT_ABSTRACT.md` §5) — the pipeline stages.
- **v2 "Work Execution Path" steps 1–5** (`docs/v2/...`) — Schemas, ASR, NLP, API, Deploy.

Your addendum states *"Phase 1 includes a multilingual voice module"* and that Phase 1's presentation
scope is *"English-prompt functionality only."* The **only** reading under which that is true is the
**five functional pipeline stages = five services = L1–L5**, where Phase 1 is the voice/ASR input stage.
That is the interpretation used throughout these documents:

| This doc's Phase | Pipeline stage | Layer | Service(s) | Owner track |
|---|---|---|---|---|
| **Phase 1** | Voice / Speech Input (ASR & normalisation) | L1+L2 | `asr-service` | Person A |
| **Phase 2** | Understanding / Intent → Schema (NLP) | L3 | `nlp-service` | Person B |
| **Phase 3** | Page Building / Layout Synthesis | L4 | `layout-service` | Person C |
| **Phase 4** | Quality Checking (Self-Healing QA) | L5 | `qa-service` | Person D |
| **Phase 5** | Publishing / Go-Live | L5 | `publish-service` (v2: fold into qa) | Person D |

> **Decision D1 (needs your confirmation):** adopt this five-phase = five-stage mapping. If instead you
> mean the v2 "Work Execution Path" 1–5, say so and these docs will be re-keyed. The rest of the analysis
> (status, scope, roadmap) does not change — only the labels do.

---

## 1. Exact five-phase architecture (extracted, not invented)

**Phase 1 — Voice / Speech Input (`asr-service`, L1+L2).**
Audio → validation → language detect → Whisper transcription → normalisation → clean transcript.
Modules: `routers/transcribe.py`, `core/{validation,language_detect,whisper_engine,normalize}.py`.
*Contains the multilingual voice module (IndicLID/IndicXlit/Indic Whisper) — the deferred item.*

**Phase 2 — Understanding (`nlp-service`, L3).**
English prompt **or** transcript → Groq Llama-3.3-70b extraction (+ regex fallback) → Pydantic
validation (2 retries) → typed `StorefrontSpec`. Modules: `routers/extract.py`,
`core/{schema_builder,schema_validator,ner_model}.py`.

**Phase 3 — Page Building (`layout-service`, L4).**
`StorefrontSpec` → template select → palette → Jinja2 render (component-assembly or monolith) →
HTML bundle (JSON-LD, WhatsApp link, responsive). Modules: `routers/{generate,scrape}.py`,
`core/{template_classifier,palette_engine,renderer,component_picker}.py`, `templates/*.jinja2`.

**Phase 4 — Quality Checking (`qa-service`, L5).**
HTML → multi-viewport Playwright + axe-core + custom checks → violation report. SORT/REPAIR/LEARN
are stubs. Modules: `routers/qa.py`, `core/{detect,sort,repair,learn}_engine.py`,
`data/constraint-rules/*.json`.

**Phase 5 — Publishing (`publish-service`, L5).**
Re-check QA pass → upload bundle to S3 → CloudFront invalidate → live URL. Modules:
`routers/publish.py`, `core/s3_uploader.py`. (Mocked; v2 wants it merged into qa-service.)

---

## 2. Phase-by-phase status & evidence audit

| Phase | Actual purpose & modules | Verified status | Presentation scope | Deferred work | Dependencies |
|---|---|---|---|---|---|
| **1 ASR** | Audio→transcript; `whisper_engine`, `language_detect`, `normalize`, `validation` | **PARTIAL / English-stub.** Boots; Groq Whisper if key else simulated; `language_detect`→"en"; no Indic normalisation | **Use English text prompt** as input; optionally pre-recorded English clip via Groq if key available | **Multilingual voice:** IndicLID, IndicXlit, IndicBERT, Hindi/Marathi Whisper validation | Groq key (optional); none hard |
| **2 NLP** | Prompt/transcript→`StorefrontSpec`; `schema_builder` (+fallback), `schema_validator` | **WORKING.** Real Groq path + regex fallback (works offline); 2-retry validation | **Complete + verify** English extraction on scripted prompts | IndicBERT NER two-pass; non-English extraction tuning | Phase 1 output *or* direct prompt (so not blocked) |
| **3 Layout** | `StorefrontSpec`→HTML; `renderer`, `palette_engine`, 5 templates, component lib | **WORKING.** 5 templates render; palettes; JSON-LD; wa.me; component-assembly for `food` | **Verify** all 5 categories; pick demo category(ies) | TF-IDF k-NN classifier; full component library (Phase B sign-off); scraping polish | Phase 2 `StorefrontSpec` shape |
| **4 QA** | HTML→violations; `detect_engine` (+ stub sort/repair/learn) | **PARTIAL.** DETECT code-complete, unit-tested w/ fake page; **real browser unverified**; repair/learn stubbed | **Verify** DETECT on fixtures + one generated page (real Chromium) → show a QA report | SORT ranking, REPAIR (FAISS), LEARN (CodeBERT), full 50-rule set | Phase 3 real HTML; Playwright+axe-core installed |
| **5 Publish** | QA-pass→S3→live URL; `s3_uploader`, `publish.py` | **GROUNDWORK.** boto3 mocked; pass-check stubbed; no AWS | **Describe as designed**; optional local static serve of the bundle as "preview URL" | Real S3+CloudFront; consolidation into qa; server-side pass re-check vs DB | Phase 4 pass; AWS creds |

---

## 3. The English-only scope decision (and why multilingual voice is deferred)

**Decision:** for the upcoming presentation, the supported interaction scope is the **English
prompt-first workflow**. Voice capture, if shown at all, uses an **English** sample/clip; the
primary, reliable path is **typed/dictated English prompt → storefront**.

**Why defer multilingual voice (honest engineering reasons):**
1. **Reliability under demo conditions.** The prompt→spec→page path already runs end-to-end and even
   works **offline** via the regex fallback — ideal when conference Wi-Fi or the Groq quota is flaky.
2. **Multilingual voice is genuinely unbuilt and uncertain.** `language_detect` is a stub; there is no
   IndicLID/IndicXlit/IndicBERT implementation; the docs flag Marathi on Groq's Whisper as unverified
   (`person_a_asr.md`, `Architect.md` L2), **and Marathi is not an officially supported language of
   Llama-3.1/3.3 for *any* hosting method** (`Architect.md` L3) — a model limitation, not a Groq one
   (Hindi *is* officially supported). Building + validating multilingual reliably exceeds the presentation
   runway and risks a visible on-stage failure.
3. **The architecture already supports deferral cleanly.** `language_detect.py` is an explicit pluggable
   interface; `routers/extract.py` already accepts both `prompt` and `transcript`. Nothing must be removed
   or restructured — multilingual voice plugs back in later with no rework.

**What is explicitly preserved (not removed):** all multilingual code, interfaces, docs, Hindi UI strings,
and the Indic design in the procedure docs. Multilingual voice is recorded as a **deliberately deferred
feature for the next presentation**, not as completed work.

---

## 4. Four-way classification of every phase's functionality

### Must complete now (essential for the main demo)
- **P2:** English prompt → valid `StorefrontSpec` on a scripted set of prompts (with Groq key for quality;
  regex fallback as the safety net). *[mostly done — needs key + verification]*
- **P3:** All 5 categories render a correct page (shop name, products+prices, WhatsApp, JSON-LD, responsive). *[mostly done — verify]*
- **Integration (demo path):** one chosen, rehearsed end-to-end path that a viewer can watch
  (prompt in → page out, with a QA report). *[new wiring — see Decision D2]*

### Must verify now (exists; demonstrate, don't rebuild)
- **P4:** DETECT on `fixture-good/bad.html` **and** one freshly-generated page using **real Chromium + axe-core**.
- **P3:** `test_all_categories` + render tests pass on a team machine.
- **Infra:** `docker compose up` boots asr/nlp/layout/qa and health endpoints respond.
- **E2E:** `tests/e2e/test_prompt_pipeline.py` passes (it should, with no key).

### Can defer (safe for after the presentation)
- **P1 multilingual voice** (IndicLID/IndicXlit/IndicBERT, Hindi/Marathi Whisper validation).
- **P1 real microphone capture** in the Flutter app (use prompt/sample path for the demo).
- **P4 self-healing** REPAIR + LEARN (FAISS/CodeBERT), SORT ranking, full 50-rule set.
- **P5 real publishing** (S3/CloudFront live URL), publish/qa consolidation.
- **P3** TF-IDF k-NN classifier; component-library Phase B expansion (needs team sign-off).

### Blocked / uncertain (needs data, creds, or a decision)
- Groq API key availability/quota (affects P1 real ASR + best-quality P2). *Mitigated by fallbacks.*
- AWS credentials + bucket policy for P5. *→ keep P5 as "designed".*
- Playwright/axe-core actually running on the demo laptop (P4). *Verify early.*
- **Presentation date** (unknown — needed to fix deadlines). *Decision D4.*
- **Team→track name mapping** (unrecorded by design). *Decision D3.*
- **Which frontend is "the demo"** — Flutter (needs wiring) vs browser/visualizer. *Decision D2.*

---

## 5. Cross-phase dependencies & critical path

```
[English prompt] → P2 nlp → P3 layout → P4 qa (→ P5 publish, deferred)
                     ▲                      ▲
         (P1 ASR optional, English)   needs P3 real HTML
```
- **Hard chain:** P4 needs P3's real HTML; P3 needs P2's `StorefrontSpec`; P2 needs a prompt (P1 optional).
- **De-risk:** P2 regex fallback removes the network/key dependency; P4 seed fixtures remove the P3
  dependency for isolated QA demos (already built, per `milestones.md` mitigation).

**Critical path (minimum for a credible demo):**
`verify P2 (prompt→spec) → verify P3 (spec→page) → wire chosen demo surface → verify P4 (page→report)
→ rehearse`. P1 multilingual and P5 publishing are **off** the critical path.

---

## 6. Prioritised roadmap (summary; full detail in `03_UPDATED_WORKING_PLAN.md`)

1. Freeze scope (this doc) + confirm Decisions D1–D5.
2. Stand up the environment: `docker compose up`; obtain/confirm Groq key (or commit to fallback-only demo).
3. Verify P2 on 3–5 scripted English prompts (food/electronics/services at least).
4. Verify P3 renders all 5 categories; choose demo category(ies).
5. Wire the demo surface (Decision D2): Flutter→live services, **or** browser preview of generated HTML
   via the visualizer/layout-service.
6. Verify P4 DETECT on a real browser against a generated page; produce a real QA report.
7. Rehearse end-to-end twice; prepare an offline fallback (regex path + pre-generated page) and a backup video.
8. Write synopsis/report sections; record target-vs-actual honestly; name deferrals.

---

## 7. Team responsibilities & proposed deadlines

Owners use the track labels (A/B/C/D). Real names (Siddhesh, Dhiren, Sarvesh, Aayush) map to tracks per
**Decision D3**. Deadlines are **proposed** (anchored to the unknown presentation date **P**, Decision D4):

| Work item | Owner | Proposed deadline |
|---|---|---|
| Confirm scope + decisions | Leader (Siddhesh) + Guide | P − 14 days |
| Environment up + Groq key decision | Person A | P − 12 days |
| P2 verification (scripted prompts) | Person B | P − 10 days |
| P3 5-category verification + demo category pick | Person C | P − 10 days |
| Demo surface wiring (per D2) | Person C + whoever owns the app | P − 7 days |
| P4 DETECT real-browser verification + report | Person D | P − 7 days |
| Synopsis/report + target-vs-actual table | All | P − 5 days |
| Rehearsals ×2 + offline fallback + backup video | All | P − 2 days |

## 8. Acceptance criteria & presentation test scenarios

**Objective acceptance criteria (demo-ready = all true):**
- A1: For ≥3 English prompts, `POST /v1/nlp/extract` returns `is_valid: true` with correct `category`
  and ≥1 product with a price.
- A2: `POST /v1/layout/generate` returns HTML containing the shop name, each product + price, a `wa.me/`
  link, a `name="viewport"` meta, and the right JSON-LD `@type`, for all 5 categories.
- A3: `POST /v1/qa/run` on a generated page returns a real violation report from a real browser render.
- A4: The whole path is shown through one rehearsed surface in < ~1 minute, and still works **offline**
  (fallback path) if the network/Groq fails.
- A5: `docker compose up` boots asr/nlp/layout/qa with healthy `/health`.

**Scripted test scenarios (use as both QA and demo scripts):**
- S1 Food: *"Create a store for The Daily Fresh Bakery — Sourdough Bread Rs 180, Chocolate Croissant 120,
  Blueberry Cheesecake 250, open Mon–Sat 8am–8pm, WhatsApp 9876543210, Bandra West Mumbai."*
  (This is already the E2E test — expect category `food`.)
- S2 Electronics: *"Rahul Electronics in Pune — smart watches 2500, power banks 999, mobile covers 199,
  WhatsApp 9123456789."* → expect `electronics`.
- S3 Services: *"Sharma Plumbing Services, Nashik — tap repair 300, pipe fitting 800, bookings on WhatsApp
  9000000000, open 9 to 7."* → expect `services`.
- S4 Negative/robustness: empty prompt → `400 EMPTY_PROMPT`; gibberish → still returns a valid (if sparse) spec.
- S5 QA: run DETECT on `fixture-bad.html` → expect ~6–7 violations; on `fixture-good.html` → ~0.

## 9. Risks & fallbacks

| Risk | Fallback |
|---|---|
| Groq key/quota/network fails on stage | Regex fallback path (no key needed) + pre-generated page + backup video |
| Playwright/axe-core won't run on laptop | Show QA on pre-captured fixtures; present DETECT output from an earlier run |
| Flutter wiring slips | Demo via browser preview of generated HTML (visualizer / direct render) |
| Panel probes "self-healing"/"published URL" | State honestly: DETECT built, REPAIR/LEARN + publish designed/deferred |
| Multilingual question | "Deliberately deferred; interfaces preserved; English baseline validated" |

## 10. Decisions requiring your approval

- **D1 — Phase mapping:** adopt the five-stage mapping in §0? (Yes/adjust.)
- **D2 — Demo surface:** (a) wire Flutter to live services, (b) browser/visualizer preview of generated
  HTML, or (c) scripted CLI/E2E + browser. *(Recommend starting with (b) for safety, add (a) if time allows.)*
- **D3 — Track→name mapping:** who is Person A/B/C/D?
- **D4 — Presentation date (P):** needed to turn proposed deadlines into real ones.
- **D5 — Groq key:** will a funded/available key be used, or do we demo on the offline fallback only?
- **D6 — Publishing claim:** present Phase 5 as "designed/deferred", or invest in a minimal real S3 publish?
- **D7 — StorefrontSpec contract:** ratify the current lenient operative schema (only `shop_name, category`
  required) as **v1.1**, or restore the frozen v1.0 required fields (`products`, `contact.whatsapp`, numeric
  `price`)? Looser = more robust demo; stricter = matches the submitted contract. *(Recommend: ratify as v1.1 and note it.)*
- **D8 — Reference paper `docs/papers/18.pdf`: RESOLVED (2026-10-11).** Identified as Othman, Dhouib &
  Al Jabor, *"Fostering websites accessibility: a case study on the use of the Large Language Models ChatGPT
  for automatic remediation"* (Mada Qatar Assistive Technology Center) — LLM-based WCAG 2.1 auto-remediation
  vs manual (WAVE) testing. Cite it under the Phase-4 self-healing-QA / LLM-repair methodology.

> After you approve D1–D8 (and authorise implementation), work proceeds per `03_UPDATED_WORKING_PLAN.md`.
> **No code will be written until then.**
