# 02 — Previous vs Latest Documentation Comparison

**Purpose:** satisfy the requirement to "read and compare previous documents against the latest
updated documents." Read-only; nothing modified.

## A. What counts as "previous" vs "latest"

| Set | Files | Role |
|---|---|---|
| **Previous / original plan** | `docs/procedure/*.md` (milestones, procedure_plan, team_phase_plan, person_a–d, Architect, api_contracts, data, security, testing, etc.) + `VoiceFront_Store_PROJECT_ABSTRACT.md` | The originally-submitted 6-month, 5-service, multilingual-voice plan |
| **Latest / operative plan** | `docs/v2/v2_architecture_and_implementation_plan.md` | The **Prompt-First English Baseline** pivot for presentation |
| **Reconciliation rule** | `VoiceFront_Store_PROJECT_ABSTRACT.md` §9 | Already states: where docs conflict, the **newer plan wins** for "what is actually being built" |

The abstract itself anticipates this split (§9 "Superseded facts — resolve conflicts this way").
The **v2 doc is the newest operative source**; the procedure docs remain correct for *intent, "why",
and future (multilingual) scope*.

## B. Point-by-point delta (previous → latest), with code evidence

| Topic | Previous (procedure docs / abstract) | Latest (v2 doc) | Code reality (audit) |
|---|---|---|---|
| **Primary input** | Voice (WebRTC capture → Whisper) | **English text prompt**; voice deferred, hooks kept | `routers/extract.py` takes `prompt` or `transcript`; `language_detect.py` → "en" |
| **ASR** | Multilingual Whisper + IndicLID + IndicXlit + BERT punctuation | Deferred modular plug-in | `whisper_engine.py` real-if-key else simulated; no Indic normalisation |
| **NER** | IndicBERT local two-pass | Deferred; unified via LLM prompt | `ner_model.py` is regex shim, unused in extract path |
| **Schema SSOT** | `storefront_spec.schema.json` (draft-07) | proposes `storefront_spec_v2.py` Pydantic | **`packages/schemas/entity_types.py`** is the live Pydantic SSOT (+ JSON Schema + TS) |
| **LLM hosting** | AWS EC2+GPU (deck) → Groq hosted (procedure) | Groq hosted | direct Groq calls in `whisper_engine.py`, `schema_builder.py` |
| **Layout classifier** | TF-IDF + k-NN over categories | LLM/direct categorisation, recalibrate | `template_classifier.py` = passthrough stub |
| **Layout source** | 5 fixed Jinja2 templates | + live component library + Scrapling scraping | 5 templates **and** `data/component-library/` + `scrape.py` + `tools/scrape_with_scrapling.py` |
| **QA / publish** | qa-service + separate publish-service (S3+CloudFront) | **Consolidate publish into qa**; simple LLM patching | publish-service still separate; S3 mocked; consolidation **not done** |
| **Containers** | (per-service) | Alpine, ~200 MB, "torch caches dead" | `python:3.12-slim`; deps lightweight (no torch) — intent met, base image differs |
| **Frontend** | `apps/web` (Next.js) + `apps/mobile` | "Bind frontend mock API to local Docker swarm" | **Flutter `voicefront/`** is the live demo app, currently **mock data** |
| **Scope of languages** | Hindi+English (Marathi stretch) | **English baseline**, multilingual deferred | English-only operative; Hindi strings/sample present but not a validated pipeline |

## C. What the v2 doc KEEPS from the original (do not treat as removed)

- The **5-stage pipeline shape** (input → NLP → layout → QA → publish) is unchanged.
- The **StorefrontSpec** contract and the 5 retail categories.
- The **self-healing QA concept** (SORT→DETECT→REPAIR→LEARN) — DETECT built, rest deferred.
- The **evaluation framework & targets** (WER, F1, WCAG, CWV, TTL) — still the yardstick.
- All **multilingual code/interfaces/docs** — retained as extension points, explicitly not deleted.

## D. Conflicts a panel might catch (pre-empt these in the report)

1. **"400+ rules" / "12 templates"** (deck) vs **50 rules / 5 templates** (MVP) vs **18 rules / 5 templates**
   (current code). State the gap honestly as target-state vs MVP vs current.
2. **"94.7% first-pass validity"** appears as a hardcoded chip in the Flutter UI — it is a *target/claim from
   the framework*, **not a measured number yet**. Do not present it as measured.
3. **"Self-healing"** currently means **DETECT only**; REPAIR/LEARN (FAISS/CodeBERT) are stubs. Say so.
4. **"Published live URL"** is not currently real (S3 mocked). Present Phase 5 as designed, not demonstrated.
5. **"Frozen StorefrontSpec v1.0"** (`data.md`: requires `products`, `contact.whatsapp`, numeric `price`) differs
   from the **operative** schema (`entity_types.py`: only `shop_name,category` required; price `number|string|null`;
   different `location` shape). Don't claim v1.0 is unchanged — ratify the operative version as **v1.1**.
6. **Data layer is designed but unbuilt** — the 7 Postgres tables + Redis in `data.md` have no implementation; the
   status enum/versioning is on paper only; the pipeline currently runs stateless against seed fixtures.
7. **Documented eval test-suite (WER/F1/WCAG/CWV/TTL) is unbuilt** — only `tests/e2e/test_prompt_pipeline.py`
   exists, so every quantitative target is currently unmeasured. Name this in the report rather than quoting targets as results.

## E. Net conclusion

The latest doc (v2) and the code **agree**: the project is a working **English prompt-first**
text→storefront pipeline with multilingual voice deliberately parked behind clean interfaces. The
procedure docs remain the authoritative source for the deferred multilingual design and the "why".
The planning in `03_...` and `07_...` is built on this reconciled understanding.
