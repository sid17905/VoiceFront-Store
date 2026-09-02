# VoiceStorefront — Step-by-Step Execution Procedure

This is `milestones.md` broken down to the step level — not "Month 1: foundations" but the
actual ordered actions inside Month 1. Each step names the file(s) it touches (per `files.md`)
so there's no ambiguity about where work happens. Steps within a phase are mostly sequential;
steps across different Tracks (A–D, per `milestones.md`) run in parallel once Phase 1 is done.

---

## PHASE 0 — Environment & Repo Setup (before any feature work)

1. Create the GitHub repo, initialize with `.gitignore`, `README.md`.
2. Run `scaffold_project.ps1` (or the bash equivalent) to generate the full folder/file tree from `files.md`.
3. Install Docker Desktop / Docker Engine on all 4 machines; confirm `docker --version` works for everyone.
4. Write `infra/docker/docker-compose.dev.yml` with stub (empty `main.py`) services first — goal is "everything boots," not "everything works."
5. Add `.env.example` in each `services/*` folder per `environment.md`; each teammate copies to their own `.env`.
6. Set up branch protection on `main` (require PR review, require CI pass) before anyone pushes real code.
7. Create the GitHub Actions skeleton in `infra/ci-cd/` — one workflow file per service, initially just running `pytest --collect-only` (proves the pipeline runs, not that tests pass yet).
8. Assign Track ownership (A: asr-service, B: nlp-service, C: layout-service, D: qa-service + publish-service) — write the assignment into `docs/milestones.md` or a shared doc, not just verbally.
9. Confirm everyone can run `docker compose -f infra/docker/docker-compose.dev.yml up --build` and hit each stub service's root endpoint.
10. Get everyone a free Groq API key; confirm one test call each (Whisper transcription + Llama-3 chat completion) — per `inference_hosting_plan.md`, this replaces any local Whisper/Ollama setup entirely.
11. Buy the project domain (~$10/year) and note it in `deployment.md` — cheap now, avoidable friction later.

---

## PHASE 1 — Foundations (Month 1)

### Shared (blocks everything else — do this first)
12. Draft `packages/schemas/storefront_spec.schema.json` per the structure in `data.md`.
13. Review the draft as a full team — this is the one artifact all 4 tracks depend on.
14. Freeze `StorefrontSpec v1.0` — tag it, do not modify without a team discussion.
15. Generate `packages/schemas/entity_types.py` and `entity_types.ts` from the same source list (`SHOP_NAME, PRODUCT, PRICE, CATEGORY, HOURS, LOCATION, CONTACT, DESCRIPTION`).
16. Write `packages/common-utils/exceptions.py` with the base `VoiceStorefrontError` and subclasses (`AsrError`, `SchemaValidationError`, `LayoutError`, `QaViolationError`, `PublishError`) per `common_references.md`.
17. Write `packages/common-utils/config.py` (shared env-var loader).
18. Write `packages/common-utils/groq_client.py` — one shared wrapper around Groq's API (transcription + chat completion calls, with rate-limit backoff), used by asr-service, nlp-service, and qa-service. One client, not three copies.

### Track A — asr-service
19. Confirm `GROQ_API_KEY` works against the Whisper endpoint with a sample Hindi and English clip. Test a Marathi clip too and record the result — don't assume it works (see `Architect.md` L2).
20. Download and prep the Mozilla Common Voice (Hindi, Marathi, Tamil) subset into `data/seed/` — used for accuracy benchmarking against Groq's out-of-the-box performance, not for fine-tuning (you can't fine-tune Groq's hosted model directly).
21. Write `core/language_detect.py` (IndicLID wrapper).
22. Write `core/whisper_engine.py` calling Groq's `whisper-large-v3` endpoint via `groq_client.py`, passing the detected language code as the `language` parameter.
23. Write `core/validation.py` — magic-byte, format, and duration checks per `security.md` (this matters more now — a bad file wastes a real Groq API call against your shared quota, not just local compute).
24. Write `routers/transcribe.py` wiring validation → language_detect → whisper_engine.
25. Write `services/asr-service/tests/unit/` tests with mocked Groq responses (never call the real API in unit tests — save the quota for integration tests).

### Track B — nlp-service
26. Set up IndicBERT base model; confirm inference runs locally (this one stays local — it's small).
27. Draft the NER fine-tuning dataset plan (which entity-tagged sentences you'll need).
28. Write `core/ner_model.py` (initially against the un-fine-tuned base model — swap later).
29. Draft 3 few-shot prompt examples in `prompts/` for the LLM schema-fill step; test them directly against Groq's `llama-3.1-8b-instant` endpoint.
30. Write `core/schema_builder.py` calling Groq (via `groq_client.py`) with transcript + NER spans + schema + few-shot examples.
31. Write `core/schema_validator.py` — JSON Schema v7 validation, 2-retry re-prompt loop (`NLP_SCHEMA_RETRY_LIMIT`).
32. Write `routers/extract.py` wiring ner_model → schema_builder → schema_validator.

### Track C — layout-service
33. Pick the first category (recommend: food — richest product-grid use case) and hand-build its Jinja2 template.
34. Write `core/palette_engine.py` with the category→colour-palette lookup for at least this one category.
35. Write `core/renderer.py` — Jinja2 render with autoescaping confirmed **on** (per `security.md`).
36. Stub `core/template_classifier.py` to always return the food template (real k-NN comes in Phase 2).
37. Write `routers/generate.py` wiring template_classifier → palette_engine → renderer.

### Track D — qa-service + publish-service
38. Draft the first 15–20 constraint rules in `data/constraint-rules/*.json` (contrast, alt-text, viewport overflow) per the format in `data.md`.
39. Set up Playwright headless Chromium locally; confirm it can render a static HTML file at the 5 target viewport widths.
40. Write a minimal `core/detect_engine.py` that runs the 15–20 rules against a rendered page and returns a violation list (no repair yet).
41. Stub `core/sort_engine.py`, `core/repair_engine.py`, `core/learn_engine.py` as pass-throughs (real logic in Phase 3–4; `repair_engine.py`'s eventual LLM fallback will also go through `groq_client.py`).
42. Write `services/publish-service/core/s3_uploader.py` against a dev S3 bucket — confirm a file uploads and is publicly readable at the right prefix only.

### Phase 1 checkpoint
43. Everyone demos their own service's health/root endpoint via `docker compose up`, and confirms their Groq calls succeed.
44. Confirm `packages/schemas` is imported correctly (not re-typed) in at least one file per service.

---

## PHASE 2 — Vertical Slice, One Category Only (Month 2)

45. Wire `apps/web/app/(dashboard)/record/page.tsx` — WebRTC capture, calls `POST /v1/asr/transcribe`.
46. Wire `apps/web/app/(dashboard)/review/page.tsx` — displays the returned `StorefrontSpec`, allows manual field edits.
47. Build `packages/api-client` — one generated client, used by both pages above (per `common_references.md`, one error-parsing function only).
48. Connect record → transcribe → extract → review, end to end, food category only.
49. Connect review (on confirm) → `POST /v1/layout/generate` → render the food template with real extracted data.
50. Manually verify the rendered page against 2–3 real sample recordings (record yourselves describing a fake shop).
51. Track A: begin retail-domain field recording (500–1,000 samples) — for evaluating how well Groq's Whisper handles real retail speech, feeding into the Month 5 self-hosted comparison.
52. Track D: get `core/detect_engine.py` running against the *real* rendered output from step 49, not just static fixtures.
53. Fix whatever the first real rendered pages reveal — expect the schema, not the code, to be the first thing that needs adjusting.

### Phase 2 checkpoint
54. Live demo: speak a shop description → see a rendered (unvalidated) storefront page. This is the first genuinely demoable milestone.

---

## PHASE 3 — QA Pipeline Comes Online (Month 3)

55. Track D: implement real `core/sort_engine.py` — failure-probability ranking (start with a simple heuristic ranking by historical rule-failure frequency; the full model can come later).
56. Track D: expand `core/detect_engine.py` to the full constraint set as rules are added (target: growing toward 50 for MVP).
57. Track D: write `services/qa-service/tests/integration/` covering detect_engine against known-bad fixtures.
58. Track A: run `test_wer.py` against the 200-utterance benchmark (`data/seed/asr_benchmark/`) through Groq — get your first real WER number. Watch the daily/per-minute rate limit; cache raw results so you don't re-call the API just to re-analyze.
59. Track B: stress-test the schema validator against deliberately messy/ambiguous transcripts; tighten the re-prompt logic.
60. Track B: write `services/nlp-service/tests/integration/test_schema_f1.py` against a growing gold-annotated set — batch the calls deliberately, Groq's free-tier per-minute limit will throttle 500 concurrent requests.
61. Track C: build out the remaining 4 category templates (apparel, electronics, pharmacy, services).
62. Track C: replace the stubbed `template_classifier.py` with the real TF-IDF + k-NN classifier across all 5 categories.
63. Wire `routers/qa.py` to actually call sort → detect and return a `QAReport` (no repair yet — `passed` may legitimately be `false` at this point).

### Phase 3 checkpoint
64. Demo: full pipeline runs across all 5 categories and produces a real (non-mocked) QA report with detected violations.

---

## PHASE 4 — Self-Healing + Publish (Month 4)

65. Track D: build the FAISS index (`IndexFlatIP`) and embed the first batch of manually-authored repair patches via CodeBERT.
66. Track D: implement `core/repair_engine.py` — FAISS similarity match (threshold 0.87) → apply patch.
67. Track D: implement the LLM-assisted repair fallback path (via `groq_client.py`) for violations with no FAISS match.
68. Track D: implement `core/learn_engine.py` — re-run detect on the patched section, write to FAISS **only** if the repair is confirmed.
69. Track D: write `test_repair_latency.py`, measuring FAISS-match and Groq-LLM-generated paths separately — expect the Groq path to be slower than the original 800ms target assumed (that target was written assuming local inference); report the real number honestly.
70. Wire `publish-service/routers/publish.py` — server-side re-check of `qa_report.passed` before allowing upload (per `api_contracts.md` precondition).
71. Wire `apps/web/app/(dashboard)/storefronts/page.tsx` — lists published storefronts with their live URLs, served from your purchased domain.
72. Run the first full end-to-end pass: voice → transcript → schema → layout → QA (with repair) → publish → live URL.
73. Time the full run against the <5-minute TTL target (`test_ttl_stopwatch.py`) — this now includes real Groq network round-trips, which is the honest number.

### Phase 4 checkpoint
74. Demo: at least one category goes voice-in to live published URL with zero critical violations remaining.

---

## PHASE 5 — Hardening + Evaluation (Month 5)

75. Run `test_wer.py`, `test_schema_f1.py` again against Groq — record real numbers against Table 5 targets.
76. Rent a GPU box for a few hours (`deployment.md` §7); re-run `test_wer.py` and `test_schema_f1.py` against genuinely self-hosted `faster-whisper` + Ollama. Record both sets of numbers side by side — this is your evidence for Table 4's "self-hostable" claim.
77. Run `test_wcag_compliance.py` (axe-core) across all 5 templates × 5 viewports.
78. Run `test_lighthouse_ci.py` against several published storefronts — confirm Core Web Vitals thresholds.
79. Security pass per `security.md`: re-verify upload validation is enforced server-side, confirm S3 bucket policy is prefix-scoped and not world-writable, add rate limiting to `/v1/asr/transcribe` and `/v1/qa/run` (protecting your shared Groq quota now, not just server load).
80. Recruit the 50-user pilot cohort; brief them and get the recording consent/disclosure sorted if audio is retained.
81. Launch the 30-day pilot window — start this as early in Month 5 as possible, per the risk flagged in `milestones.md`.
82. Set up client-side error-beacon logging on published storefronts to track the post-publish error rate metric during the pilot.
83. Fix any critical bugs surfaced by early pilot users immediately — don't batch pilot-reported bugs for Month 6.

### Phase 5 checkpoint
84. Every automated metric in the evaluation framework has been measured at least once with real numbers (both Groq-hosted and self-hosted), and the pilot is live and collecting data.

---

## PHASE 6 — Report, Defense Prep, Pilot Close-Out (Month 6)

85. Close the 30-day pilot window; pull NPS survey results, task-completion rate, and post-publish error rate.
86. Compile a target-vs-actual table for every row in Table 5/Table 6 of the original framework — include the gaps, don't hide them.
87. Freeze the codebase (tag a release) — no further feature changes past this point, bug fixes only.
88. Write the final report: theoretical framework (already have this) + implementation results + evaluation numbers + limitations actually encountered (vs. the ones anticipated in the original scope section) — including the Groq-vs-self-hosted comparison from step 76.
89. Prepare the live demo script — decide in advance which category/recording you'll use, and have a pre-recorded backup video in case live ASR, Groq, or network fails during defense.
90. Rehearse the full demo at least twice on the actual defense hardware/network, not just a laptop at home.
91. Prepare answers in advance for the hardest predictable panel questions: "why EC2, CPU-only, not GPU" (`deployment.md` has the answer), "why Groq instead of self-hosting" (`inference_hosting_plan.md` has the answer — the Month 5 validation run is your evidence), and "what does self-healing actually learn" (`Architect.md`'s cross-cutting note has the answer — don't overstate it).
92. Final submission.

---

## Cross-phase notes
- Steps within a Track are sequential; steps *across* Tracks A–D in the same phase are meant to run in parallel — that's the entire point of splitting ownership in `milestones.md`.
- If a step is blocked (e.g., Track D's step 52 needs Track C's step 49 done first), that dependency is already called out in `milestones.md`'s risk section — check there before assuming something is stuck by accident.
- Don't skip the checkpoints (43, 54, 64, 74, 84) even under time pressure — they're the only points where "it works for me locally" gets tested against "it works when someone else touches it."
- Every Groq-dependent step in this plan shares one team quota — if two people are both running integration tests at the same time, expect throttling. Stagger heavy test runs (steps 58, 60 especially) rather than running them simultaneously.
