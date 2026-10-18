# 03 — Updated Working Plan

**Project:** VoiceFront Store · **Date:** 2026-10-11 · **Mode:** planning only (no code written yet).
Read with `07_FIVE_PHASE_SCOPE_AND_PRESENTATION_PLAN.md` (scope) and `01_PROJECT_AUDIT.md` (evidence).
Deadlines are **proposed**, anchored to the presentation date **P** (unknown — Decision D4 in `07_`).
Owners are track labels A–D; real-name mapping is Decision D3.

---

## Part I — Five-Phase Execution Plan for the Upcoming Presentation

> Phase mapping (five pipeline stages) is defined and flagged for confirmation in `07_` §0.

### Phase 1 — Voice / Speech Input (`asr-service`)
- **Modules / paths:** `services/asr-service/{main.py, routers/transcribe.py,
  core/validation.py, core/language_detect.py, core/whisper_engine.py, core/normalize.py}`, `.env.example`.
- **Verified status:** PARTIAL / English-stub. Service boots; real Groq Whisper only if `GROQ_API_KEY`
  set, else simulated transcript; `language_detect`→"en"; no Indic normalisation.
- **Complete for presentation:** nothing new required if the demo uses a **typed English prompt**.
  *If* a voice moment is wanted: confirm one **English** clip transcribes via Groq (needs key).
- **Verify only:** `/health`; `POST /v1/asr/transcribe` returns the `{transcript, language, confidence,
  segments}` shape on a sample clip (or simulated path).
- **Excluded this iteration:** IndicLID language detection, IndicXlit transliteration, IndicBERT,
  Hindi/Marathi Whisper validation, real mic capture.
- **Dependencies:** optional Groq key; none hard (prompt path bypasses ASR).
- **Order:** last (optional enhancement) — off the critical path.
- **Owner:** Person A. **Effort:** 0.5 day (verify-only) / +1 day if adding an English voice clip.
  **Proposed deadline:** P − 12 days.
- **Acceptance:** transcribe endpoint returns a valid response for one English input; OR explicitly
  "prompt-only, ASR deferred" is recorded.
- **Tests/evidence:** manual curl of `/v1/asr/transcribe`; screenshot of response.
- **Risks/fallback:** no key → simulated/transcript-less; demo uses prompt input instead.

### Phase 2 — Understanding / Schema Extraction (`nlp-service`)
- **Modules / paths:** `services/nlp-service/{main.py, routers/extract.py,
  core/schema_builder.py, core/schema_validator.py, core/ner_model.py}`, `.env.example`.
- **Verified status:** WORKING. Real Groq Llama-3.3-70b with JSON system prompt + 2-retry validation
  loop; `_heuristic_fallback_extractor` makes it work **with no key / offline**.
- **Complete for presentation:** confirm quality on the scripted prompts; set `GROQ_MODEL`/key via env;
  make sure fallback output is "demo-clean" for S1–S3.
- **Verify only:** `POST /v1/nlp/extract` returns `is_valid: true`, correct `category`, ≥1 priced product
  for S1–S3; empty prompt → `400 EMPTY_PROMPT`.
- **Excluded:** IndicBERT NER two-pass; non-English extraction tuning.
- **Dependencies:** a prompt (or Phase 1 transcript). Not blocked by Phase 1.
- **Order:** FIRST on the critical path.
- **Owner:** Person B. **Effort:** 1 day (verify + prompt tuning). **Proposed deadline:** P − 10 days.
- **Acceptance:** A1 in `07_` §8 — ≥3 prompts extract valid specs.
- **Tests/evidence:** `tests/e2e/test_prompt_pipeline.py`; `test_schema_f1.py` (if key/data);
  saved JSON specs for S1–S3.
- **Risks/fallback:** Groq down → regex fallback (pre-validate its S1–S3 output looks good).

### Phase 3 — Page Building / Layout Synthesis (`layout-service`)
- **Modules / paths:** `services/layout-service/{main.py, routers/generate.py, routers/scrape.py,
  core/template_classifier.py, core/palette_engine.py, core/renderer.py, core/component_picker.py,
  templates/*.jinja2}`, `data/component-library/`.
- **Verified status:** WORKING. 5 templates + 5 palettes; JSON-LD; `wa.me/`; responsive CSS;
  component-assembly path (complete for `food`, partial elsewhere → monolith fallback).
- **Complete for presentation:** pick demo category(ies); ensure component-library variants used are
  `review_status: APPROVED`; confirm fallback-to-monolith is clean for non-food.
- **Verify only:** `POST /v1/layout/generate` for all 5 categories (A2 criteria);
  `test_all_categories.py` passes.
- **Excluded:** TF-IDF k-NN classifier; component-library Phase B expansion (needs team sign-off per
  `PHASE_B_COMPONENT_LIBRARY_PROPOSAL.md`); scraping feature polish.
- **Dependencies:** Phase 2 `StorefrontSpec` shape (stable — `entity_types.py`).
- **Order:** SECOND on the critical path.
- **Owner:** Person C. **Effort:** 1 day (verify + category choice). **Proposed deadline:** P − 10 days.
- **Acceptance:** A2 — all 5 categories render required elements.
- **Tests/evidence:** `test_all_categories.py`, `test_render.py`; saved generated `.html` per category.
- **Risks/fallback:** component variant missing → monolithic template still renders a valid page.

### Phase 4 — Quality Checking (`qa-service`)
- **Modules / paths:** `services/qa-service/{main.py, routers/qa.py,
  core/detect_engine.py, core/sort_engine.py, core/repair_engine.py, core/learn_engine.py}`,
  `data/constraint-rules/*.json`, `data/seed/rendered_bundles/fixture-{good,bad}.html`.
- **Verified status:** PARTIAL. DETECT code-complete (multi-viewport axe-core + custom), unit-tested with a
  fake page; **real Chromium/axe-core unverified** (see `PERSON_D_README.md`). SORT/REPAIR/LEARN stubbed.
- **Complete for presentation:** install Playwright Chromium + axe-core on the demo laptop; run DETECT once
  against a generated page to produce a **real** report to show.
- **Verify only:** `python core/detect_engine.py ../../data/seed/rendered_bundles/fixture-bad.html`
  (~6–7 violations) and `fixture-good.html` (~0); `POST /v1/qa/run` returns a `QaReport`.
- **Excluded:** SORT ranking, REPAIR (FAISS), LEARN (CodeBERT), the full 50-rule set.
- **Dependencies:** Phase 3 real HTML (or seed fixtures); Playwright+axe-core installed.
- **Order:** THIRD on the critical path.
- **Owner:** Person D. **Effort:** 1 day (install + verify). **Proposed deadline:** P − 7 days.
- **Acceptance:** A3 + S5 — a real violation report from a real browser render.
- **Tests/evidence:** QA report JSON for a generated page + fixtures; screenshot/log of the run.
- **Risks/fallback:** browser won't install → present DETECT output captured earlier on another machine.

### Phase 5 — Publishing / Go-Live (`publish-service`)
- **Modules / paths:** `services/publish-service/{routers/publish.py, core/s3_uploader.py}`.
- **Verified status:** GROUNDWORK ONLY. boto3 mocked; pass re-check stubbed `True`; no AWS; not in compose;
  v2 wants it merged into qa-service.
- **Complete for presentation:** **none** (recommended) — present Phase 5 as designed. *Optional (D6):* a
  minimal real S3 upload of one bundle to show a live URL, or a local static-serve "preview URL".
- **Verify only:** `test_s3_uploader.py` (mocked) passes.
- **Excluded:** real S3+CloudFront, consolidation into qa, DB-backed pass re-check.
- **Dependencies:** Phase 4 pass; AWS creds + bucket policy.
- **Order:** last — off the critical path.
- **Owner:** Person D. **Effort:** 0 (describe) / 1–2 days if doing a minimal real publish.
- **Acceptance:** architecture explained with the never-trust-client re-check; OR (optional) one real
  public URL serves the bundle.
- **Tests/evidence:** design slide; (optional) a working URL.
- **Risks/fallback:** no AWS → local `python -m http.server` on the bundle as a stand-in "preview".

---

## Part II — Critical-path plan (minimum for a working presentation)

```
D1–D6 approved
  → ENV up (compose + Groq key decision)        [A]        P-12
  → P2 verify prompt→spec (S1–S3)               [B]        P-10   ─┐ critical
  → P3 verify spec→page (5 categories)          [C]        P-10    │
  → wire demo surface (D2)                      [C/app]    P-7     │
  → P4 verify page→report (real browser)        [D]        P-7    ─┘
  → rehearse ×2 + offline fallback + video      [all]      P-2
```
Everything **not** on this line (P1 multilingual voice, P4 self-healing, P5 real publish, k-NN classifier,
component-library Phase B) is deferred and must not block the path above.

---

## Part III — Files that WOULD be touched during implementation (NOT modified now)

> Listed so the team can plan; **no edits are made in this planning pass.**

- **Config/env (likely):** each `services/*/.env` (local, from `.env.example`); root `.env` for compose
  (`GROQ_API_KEY`, `GROQ_MODEL`).
- **P2 verify/tune:** `services/nlp-service/core/schema_builder.py` (prompt wording / fallback polish only if needed).
- **P3 verify:** `services/layout-service/core/component_picker.py` / `data/component-library/*.json`
  (only if a chosen category's variants need `APPROVED` status) ; `templates/*.jinja2` (cosmetic only if needed).
- **Demo surface (D2):** if Flutter → `voicefront/lib/services/groq_api_service.dart` +
  `screens/{record,review_edit,preview_qa}_screen.dart` to call real endpoints instead of mock data;
  if browser → reuse `docs/procedure/pipeline-visualizer.html` / `layout-service` directly (no app changes).
- **P4 verify:** none to source — environment install (Playwright Chromium, `npm i axe-core`).
- **Housekeeping (optional, low priority):** fill `README.md`; decide `common-utils` vs `common_utils`;
  remove/relocate stray `docs/HACKERHOUSE _NEXT.txt`.
- **New (only if approved):** a tiny `scripts/demo_pipeline.py` or Make target to run S1–S3 end-to-end for rehearsal.

---

## Part IV — Effort roll-up & sequencing

| # | Task | Owner | Depends on | Effort | Proposed |
|---|---|---|---|---|---|
| 1 | Approve scope + D1–D6 | Leader+Guide | — | — | P−14 |
| 2 | Env up + key decision | A | 1 | 0.5d | P−12 |
| 3 | P2 verify (S1–S3) | B | 2 | 1d | P−10 |
| 4 | P3 verify 5 categories | C | 2 | 1d | P−10 |
| 5 | Wire demo surface (D2) | C/app | 3,4 | 1–3d | P−7 |
| 6 | P4 real-browser verify | D | 4 | 1d | P−7 |
| 7 | (opt) P1 English voice clip | A | 2 | 1d | P−7 |
| 8 | (opt) P5 minimal publish | D | 6 | 1–2d | P−5 |
| 9 | Synopsis/report + target-vs-actual | all | 3,4,6 | 1d | P−5 |
| 10 | Rehearse ×2 + fallback + video | all | 5,6 | 1d | P−2 |

**Critical path = 1→2→3→4→5→6→10.** Items 7, 8 are optional; defer if time is tight.

---

## Part V — Definition of "presentation-ready" (vs full completion)

Presentation-ready = criteria **A1–A5** (`07_` §8) met on the chosen demo surface, with an offline
fallback and backup video. This is **not** full project completion — multilingual voice, self-healing
repair/learn, and real publishing remain future work and must be named as such in the report and viva.

---

## Part VI — Practical demo logistics (from `hardware.md`, added after deep-read)

- **Run the demo + full local stack on Person C's machine** (RTX 4050 / 16 GB — the strongest on the team;
  `hardware.md`). **Not** Person D's (2 GB VRAM / 8 GB RAM — the tightest *and* the most loaded role) — running
  the whole Docker Compose there will swap.
- **Give Person D shared-staging/Groq access before QA verification.** Their laptop can't run Whisper/LLM
  locally; Playwright is CPU-OK but RAM-tight, so verify P4 on Person C's machine or staging.
- **Reconcile the StorefrontSpec contract (D7)** before wiring the app, so nlp validation strictness and the
  app's expected fields agree — the frozen v1.0 and the operative schema currently differ (see `01_` §9.9, `02_` D5).
- **The data layer (Postgres/Redis) is unbuilt** — the demo runs **stateless** against seed fixtures. Don't
  promise persistence, "my storefronts" history, or server-side QA re-check from a DB in the demo narrative.
- **Evaluation numbers:** the documented WER/F1/WCAG/CWV/TTL tests don't exist yet (`01_` §7 note). Either build
  the two cheapest to demo (`test_wcag_compliance.py` via axe-core on a generated page, `test_ttl_stopwatch.py`)
  **or** present those targets as "designed, not yet measured" — do not quote targets as if they were results.
