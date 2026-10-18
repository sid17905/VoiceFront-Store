# 00 — Planning & Audit Package (INDEX)

**Project:** VoiceFront Store · **Prepared:** 2026-10-11 · **Mode:** PLANNING / AUDIT / DOCUMENTATION ONLY.
**No application source files were created or modified.** All files here are new planning docs (now in
`docs/_planning_audit/`).

## The photographed forms (what the images are)
The 6 images in `docs/` are the **Major Project Diary — Guide Meeting & Weekly Progress Record** forms,
Sem VII (AI & DS), pages 17–22, one per week, with pre-printed weekly task themes:

| Image | Page | Week | Pre-printed task |
|---|---|---|---|
| ...16.18.12.jpeg | 17 | 07 | Requirements specification: functional, non-functional & dataset identification |
| ...16.18.13.jpeg | 18 | 08 | Module-wise architecture design, data pipeline design & model selection strategy |
| ...16.18.13 (1).jpeg | 19 | 09 | Implementation platform setup: cloud/local, framework & library configuration |
| ...16.18.13 (2).jpeg | 20 | 10 | Study & hands-on exploration of AI/ML tools, libraries & frameworks |
| ...16.18.14.jpeg | 21 | 11 | Partial implementation: data preprocessing, feature engineering & baseline model |
| ...16.18.14 (1).jpeg | 22 | 12 | Documentation of Synopsis: problem statement, literature review, methodology & timeline |

→ Diary drafts for all six weeks are in **`04_MAJOR_PROJECT_DIARY_WEEKS_07-12.md`**.

## Documents in this package
| File | What it is |
|---|---|
| `00_INDEX.md` | This index. |
| `01_PROJECT_AUDIT.md` | Evidence-based status of docs, every service, frontend, infra, tests, risks. |
| `02_DOCS_COMPARISON_PREVIOUS_VS_LATEST.md` | Original procedure docs vs the v2 Prompt-First pivot, with code evidence. |
| `03_UPDATED_WORKING_PLAN.md` | Execution roadmap incl. **"Five-Phase Execution Plan for the Upcoming Presentation"**, critical path, effort, files that *would* be touched. |
| `04_MAJOR_PROJECT_DIARY_WEEKS_07-12.md` | Six handwrite-ready diary entries matching the forms. |
| `07_FIVE_PHASE_SCOPE_AND_PRESENTATION_PLAN.md` | **Master** scope doc: phase table, English-only decision + justification, complete/verify/defer/investigate, dependencies, roadmap, acceptance criteria, test scenarios, decisions needing approval. |

> Numbering follows the scheme your addendum referenced (`03_…`, `07_…`). The exact filenames of any
> earlier-requested set weren't available to me, so I used a clean 01–04 + 07 set — happy to re-number
> or rename to match an existing set.

## The 60-second picture
- **Working & demoable:** English **prompt → `StorefrontSpec` (NLP) → HTML page (Layout) → QA DETECT report** —
  and the prompt→page path even runs **offline** (regex fallback).
- **Deliberately deferred (English-only scope):** multilingual **voice** (IndicLID/IndicXlit/IndicBERT,
  Hindi/Marathi Whisper), QA **self-healing** repair/learn, **real publishing** to S3/CloudFront. Interfaces
  preserved; nothing removed.
- **Biggest gap for a live demo:** the Flutter app is a polished UI on **mock data**, not wired to the backend.
- **Mostly integration + verification, not new features**, is what stands between here and a credible demo.

## Decisions awaiting your approval (detail in `07_` §10)
- **D1** Confirm the five-phase = five-pipeline-stage mapping (ASR / NLP / Layout / QA / Publish).
- **D2** Demo surface: wire Flutter ↔ live services, or browser/visualizer preview of generated HTML, or scripted E2E.
- **D3** Map team names → tracks A/B/C/D.
- **D4** Presentation date (to turn proposed deadlines into real ones).
- **D5** Groq key available, or demo on the offline fallback only?
- **D6** Present Phase 5 publishing as "designed/deferred", or build a minimal real publish?
- **D7** StorefrontSpec contract: ratify the lenient operative schema as **v1.1**, or restore frozen v1.0 required fields?
- **D8** ~~Identify reference paper `docs/papers/18.pdf`~~ **RESOLVED** — Othman et al., *ChatGPT for automatic WCAG remediation* (Mada Qatar). Cite under Phase-4 QA/LLM-repair.

## Deep-read addendum (2026-10-11)
After your request, I read **every** project markdown file in full (all `docs/procedure/*.md`, both stray
Flutter READMEs). Significant new findings were folded into `01_` §9 (items 9–16) and `02_` §D (items 5–7):
**StorefrontSpec v1.0-frozen vs operative drift**, **API-contract drift**, **persistence layer (Postgres/Redis)
is design-only**, **the documented WER/F1/WCAG/CWV/TTL eval suite doesn't exist**, **`groq_client.py` mandated
but missing**, **the Flutter app is an undocumented new frontend**, and a **templates-path mismatch**. Practical
demo/hardware logistics were added to `03_` Part VI. One paper (`18.pdf`) remains unidentified (poppler not
installed, so it couldn't be read) → decision D8.

## Status
Planning complete. **Awaiting your approval of the plan and explicit authorisation before any code is written.**
