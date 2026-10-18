# 04 — Major Project Diary · Weeks 07–12 (Drafts)

**For:** Sem VII Guide Meeting Record & Weekly Progress Record forms (Smt. Indira Gandhi College of
Engineering, Ghansoli — AI & DS). One page per week; task headings are **pre-printed on the forms**
(from the photographed pages 17–22). Content below is sized to **handwrite** into the blanks.

**How to use:** copy A/B/C sections into each week's form. Fill **Meeting Date & Time / Venue /
Duration / Signatures** yourself — I have no record of those (left as `____`). Items marked
**[verify]** are proposed and need the team to confirm against what actually happened.

**Guide:** Dr. Sunil Chavan · **Team:** Siddhesh Gangurde (Leader), Dhiren Achrekar, Sarvesh Dhanrale,
Aayush Tanwar · **Track labels** A=asr, B=nlp, C=layout, D=qa/publish (map names → tracks, Decision D3).

> Scope reflected throughout: **English prompt-first baseline**; **multilingual voice deferred** to the
> next presentation (interfaces preserved, nothing removed). Deferred features are **not** shown as done.

---

## Week 07 — Requirements specification: functional, non-functional & dataset identification
*Meeting Date & Time: ____ · Venue: ____ · Duration: ____*

**A. Work Done This Week**
1. Fixed functional requirements: English prompt/voice → structured `StorefrontSpec` → responsive
   storefront → QA report, across 5 categories (food, apparel, electronics, pharmacy, services).
2. Fixed non-functional requirements: <5-min speech-to-page target, WCAG 2.2 AA, Core Web Vitals,
   Groq-hosted inference (no local GPU), stateless audio handling.
3. Identified datasets: Common Voice (Hi/Mr/Ta) for ASR *benchmarking* (not training); English retail
   prompt samples; WCAG/axe constraint-rule set; design-reference component library.
4. Confirmed entity list: SHOP_NAME, PRODUCT, PRICE, CATEGORY, HOURS, LOCATION, CONTACT, DESCRIPTION.

**B. Discussion / Outcome / Challenges**
1. Marathi ASR on Groq is unverified → scoped as stretch, not committed. [verify]
2. Agreed `StorefrontSpec` is the single frozen contract every module depends on.
3. Datasets are for measuring accuracy, not fine-tuning (Groq hosted model isn't fine-tunable).
4. MVP has no auth; rate-limiting is the main abuse/quota control.

**C. Action Items for Next Week** (No. · Task · Assigned To · Deadline)
1. Draft `StorefrontSpec v1.0` JSON Schema · B · W08
2. Draft module-wise architecture diagram · All · W08
3. Collect 5+ English shop descriptions · A · W08
4. Shortlist literature (ASR/NER/layout/WCAG) · All · W12

---

## Week 08 — Module-wise architecture design, data pipeline design & model selection strategy
*Meeting Date & Time: ____ · Venue: ____ · Duration: ____*

**A. Work Done This Week**
1. Defined the five-stage pipeline → services: (1) ASR, (2) NLP, (3) Layout, (4) QA, (5) Publish.
2. Designed data pipeline: prompt/transcript → `StorefrontSpec` (Pydantic + JSON Schema) → HTML bundle →
   QA violations → (publish).
3. Model selection: Groq Whisper-large-v3 (ASR), Groq Llama-3.3-70b (extraction), Jinja2 (layout),
   Playwright + axe-core (QA); IndicBERT/IndicLID noted for future multilingual.
4. Froze `StorefrontSpec v1.0` (shop_name, category[5], products, hours, location, contact).

**B. Discussion / Outcome / Challenges**
1. Chose Groq hosted API over local GPU (team hardware was the blocker).
2. Schema is imported, never re-typed, by every service.
3. Layout template-classifier starts as a passthrough stub; k-NN later.
4. QA self-healing (SORT→DETECT→REPAIR→LEARN) designed; only DETECT targeted first.

**C. Action Items for Next Week**
1. Stand up Docker Compose + FastAPI stubs (4 services) · A + All · W09
2. Build palette engine + first (food) template · C · W09
3. Draft 15–20 constraint rules · D · W09
4. Draft + test few-shot extraction prompt on Groq · B · W09

---

## Week 09 — Implementation platform setup: cloud/local, framework & library configuration
*Meeting Date & Time: ____ · Venue: ____ · Duration: ____*

**A. Work Done This Week**
1. Configured Docker Compose (asr:8001, nlp:8002, layout:8003, qa:8004) on `python:3.12-slim`;
   `/health` endpoints responding.
2. Set up FastAPI + Pydantic v2 per service; root `pytest.ini` (pythonpath + async mode).
3. Configured Groq access + `.env.example` per service (`GROQ_API_KEY`, `GROQ_MODEL`, `PORT`).
4. Scaffolded Flutter app (`voicefront/`); kept dependencies lightweight (no torch/transformers).

**B. Discussion / Outcome / Challenges**
1. `common-utils` (hyphen) isn't importable → used `common_utils` (underscore) + fallbacks; tidy-up pending.
2. Confirmed no local Whisper/Ollama needed — all inference via Groq.
3. Groq free-tier rate limits noted → stagger heavy test runs.
4. Each member to confirm `docker compose up` works on their machine. [verify]

**C. Action Items for Next Week**
1. Implement NLP `schema_builder` + validator (English prompt-first) · B · W10
2. Implement layout `renderer` + 5 templates · C · W10
3. Implement QA `detect_engine` + seed fixtures · D · W10
4. Hands-on exploration of Groq SDK / Jinja2 / Playwright · All · W10

---

## Week 10 — Study & hands-on exploration of AI/ML tools, libraries & frameworks
*Meeting Date & Time: ____ · Venue: ____ · Duration: ____*

**A. Work Done This Week**
1. Hands-on Groq SDK: Whisper transcription + Llama chat with JSON mode and retry/backoff.
2. Explored Jinja2 (autoescaping as a security control) and Playwright multi-viewport + axe-core WCAG checks.
3. Explored Pydantic/JSON-Schema validation and Scrapling (design-reference scraping → component library idea).
4. Reviewed deferred tech: IndicLID / IndicXlit / IndicBERT (multilingual) and FAISS + CodeBERT (self-healing) —
   studied, not adopted this iteration.

**B. Discussion / Outcome / Challenges**
1. Adopted an **English prompt-first baseline** for demo reliability; multilingual-voice tools kept as
   pluggable interfaces and **deferred to the next presentation** (ref `docs/v2`). [verify exact meeting]
2. Jinja2 logic-less rendering confirmed as the anti-injection control.
3. axe-core/Playwright need a real browser install — noted as an environment caveat.
4. FAISS/CodeBERT repair is heavy → deferred past the demo.

**C. Action Items for Next Week**
1. Build prompt→spec baseline + offline fallback · B · W11
2. Build spec→page baseline (5 categories) · C · W11
3. Build DETECT baseline against fixtures · D · W11
4. Wire the end-to-end prompt-pipeline test · B + All · W11

---

## Week 11 — Partial implementation: data preprocessing, feature engineering & baseline model
*Meeting Date & Time: ____ · Venue: ____ · Duration: ____*

**A. Work Done This Week**
1. NLP baseline: English prompt → Groq Llama extraction with 2-retry validation **and** a regex fallback
   that works offline.
2. Data preprocessing: transcript normalisation (whitespace/currency/phone) + Pydantic schema-validation loop.
3. Feature engineering: strict JSON system prompt + entity/price/phone heuristics + category inference.
4. Baseline pipeline working: layout render (5 templates, palettes, JSON-LD, WhatsApp link) + QA DETECT
   (18 rules, multi-viewport); end-to-end prompt→page test passes.

**B. Discussion / Outcome / Challenges**
1. Baseline is English prompt-first; multilingual voice deferred, interfaces preserved (`language_detect`→"en").
2. Flutter app still on **mock data** — not yet wired to live services (main integration gap for the demo).
3. Playwright/axe-core not yet verified on a real browser — pending team hardware.
4. Self-healing REPAIR/LEARN and real publishing remain stubbed (expected at baseline stage).
5. Figures like "94.7%" are target claims, **not measured** yet — to benchmark later.

**C. Action Items for Next Week**
1. Verify prompt→spec on 3+ scripted prompts · B · W12
2. Verify 5-category render + pick demo category · C · W12
3. Verify DETECT on a real browser + fixtures · D · W12
4. Draft synopsis (problem / lit review / methodology / timeline) · All · W12

---

## Week 12 — Documentation of Synopsis: problem statement, literature review, methodology & timeline
*Meeting Date & Time: ____ · Venue: ____ · Duration: ____*

**A. Work Done This Week**
1. Problem statement: <23% of 340M micro-retailers have a digital storefront — an interface (not
   connectivity) gap; a voice/prompt-to-storefront builder addresses it.
2. Literature review compiled (~20 refs in `docs/papers`: Whisper, Vistaar/IndicVoices, GPT-NER,
   guided generation, Design2Code, WCAG 2.2, LLM-based WCAG remediation (ChatGPT), program-repair, continual learning).
3. Methodology documented: five-stage pipeline (ASR→NLP→Layout→QA→Publish), Groq-hosted models,
   English prompt-first baseline with deferred multilingual voice.
4. Timeline + evaluation framework recorded (WER<5%, F1>0.90, WCAG>99%, CWV, TTL<5min) as **targets**,
   with a target-vs-actual table to be filled after measurement.

**B. Discussion / Outcome / Challenges**
1. Synopsis records the English-only presentation scope; multilingual voice listed as future work.
2. Agreed to name gaps honestly: 18 vs 50 vs 400 rules; DETECT-only self-healing; publishing designed-not-demoed.
3. Presentation date needed to lock the rehearsal schedule. [verify with guide]
4. Confirm synopsis format matches the college template. [verify]

**C. Action Items for Next Week**
1. Finalise demo surface + rehearse twice · All · before presentation
2. Prepare offline fallback + backup demo video · A + D · before presentation
3. Fill target-vs-actual table with measured numbers · All · before presentation
4. Submit synopsis to guide for review · Leader · W13 [proposed]

---

### Notes for the diary (read before copying)
- Weeks 07–12 describe **foundational** work (requirements → architecture → platform → tools → baseline →
  synopsis). The more advanced items (self-healing repair, real publish, multilingual voice) are correctly
  shown as **designed/deferred**, never as finished.
- Anything marked **[verify]** (meeting dates, who booted compose, exact scope-decision meeting, synopsis
  template) must be confirmed by the team before writing it into the official forms.
