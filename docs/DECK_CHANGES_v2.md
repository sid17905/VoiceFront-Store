# VoiceStorefront v2 — Deck Change Plan (PPT + PDF)

**Files reviewed:** `VoiceStorefront_v2 (1).pptx` (11 slides) and `VoiceStorefront_v2 (2).pdf` (11 pages — same content).
**Reviewed against:** the repo at commit `2428a6f` + working tree, 18 Oct 2026.
**Rule applied:** every number on a slide is either (a) measured from the code, or (b) labelled *target* / *future*. No claim may exceed what the repo can demonstrate on demand.

> The PDF is an export of the PPT. Fix the PPT, re-export, and both are done. Nothing in this document needs to be done twice.

---

## 0. Priority summary

| # | Issue | Severity | Where |
|---|---|---|---|
| 1 | Architecture diagram describes a system that does not exist (IndicBERT, IndicLID, IndicXlit, Llama-88B, k-NN/12 templates, Postgres, Redis, EC2 GPU, CloudFront) | **Critical** — panel will probe it | Slide 4 |
| 2 | "400+ rules" on the QA slide vs "50 constraints" on Scope vs **18 rules in code** | **Critical** — three numbers for one thing | Slides 3 & 5 |
| 3 | "SORT → DETECT → REPAIR → LEARN" presented as built; SORT is a pass-through, LEARN is a no-op, REPAIR is not wired into `/v1/qa/run` | **Critical** — headline claim | Slides 1 & 5 |
| 4 | Model table names Gemma-2-9B via Ollama; the code calls Groq `llama-3.3-70b-versatile` | **High** | Slide 6 |
| 5 | "Google Maps embed" claimed in scope; no map embed exists in any template or the renderer | **High** | Slide 3 |
| 6 | "Hindi + English ASR" in scope; `language_detect.py` returns `"en"` unconditionally | **High** | Slide 3 |
| 7 | Page numbers broken (2,3,4,5,6,11,16,15,15) and slide 9 duplicates slide 8's table | Medium | All |
| 8 | "WC3" typo; second-person coaching text in the literature table | Medium | Slide 8 |
| 9 | Budget slide is a pasted screenshot with corrupted chart axis labels | Medium | Slide 7 |
| 10 | No implementation-status, results, demo, or future-scope slide | Medium | Deck structure |

---

## 1. Slide-by-slide changes

### Slide 1 — Title
- **Subtitle:** "Voice-to-Storefront Platform with **Autonomous Self-Healing QA**" → **"Voice-to-Storefront Platform with Automated Accessibility QA and LLM-Assisted Repair"**.
  *Why:* "autonomous self-healing" implies a closed repair-and-learn loop; DETECT is real, REPAIR is written but not called by the router, SORT and LEARN are stubs. The softer subtitle is still accurate and still impressive.
- Add each member's track next to their name (ASR / NLP / Layout / QA+Publish) — the guide will ask who built what.
- **Programme-year mismatch:** the deck is correct — **B.E. Major Project, AY 2026–27**. The supplied report template (`T.E.-Project-Report-25-26.docx`) is a T.E./minor-project template whose certificate says "SE Mini Project" and whose title page says "Academic Year 2025 – 26". Use **B.E. Major Project · AY 2026–27** everywhere; see `PROJECT_REPORT_BE.md`.
- The `(20)`, `(01)`, `(16)`, `(64)` after names are unexplained — replace with roll-number labels or delete.

### Slide 2 — Problem Statement & Research Objectives
- Three uncited statistics. Add a source line under each, or soften:
  - "broadband exceeds 61% in Tier 2/3 cities" → cite (TRAI / IAMAI-Kantar).
  - "fewer than 23% of India's **340 million** micro-retailers" → **verify this number before the viva.** Widely cited Indian figures are ~13 M kirana stores and ~63 M MSMEs; 340 M reads as a typo or a global figure. Either cite the source or replace with a defensible number.
  - "ONDC's 30M-seller goal" → cite the ONDC strategy paper.
- Objective 1 names `Whisper-large-v3 + IndicXlit / IndicLID`. Keep it as a *research* objective only if the literature slide says these are benchmarked, not deployed. The implemented ASR is Whisper via Groq with `language_detect → "en"`.
- Objective 4: "(Sort → Detect → Repair → Learn)" → **"(Detect → Repair, with Sort and Learn as future work)"**. If REPAIR gets wired before the viva, use "(Detect → Repair)".
- Objective 5 ("publish … in under 10 minutes"): either time one run and put the real figure here, or write "target: end-to-end generation in under 10 minutes".

### Slide 3 — Scope & SDG Alignment
| Current text | Change to | Why |
|---|---|---|
| "Hindi + English ASR (Marathi stretch)" | "English voice or text input; Hindi UI strings; multilingual ASR = next semester" | `language_detect` returns `en`; no Hindi ASR path is validated |
| "5 retail category templates" | Keep — but see Slide 4. All 5 templates exist; the live renderer currently emits one shared page shell parameterised by palette | 5 `.jinja2` files exist but are not rendered at runtime |
| "50 rule-based QA constraints" | "**18** QA constraints implemented (10 axe-core + 8 custom); **50** is the MVP target" | `data/constraint-rules/` holds exactly 18 JSON files |
| "Static hosting on S3 + CloudFront" | "S3 static hosting (implemented code); CloudFront = designed, Terraform resource not yet declared" | `s3_cloudfront.tf` has the bucket + policy, **no** `aws_cloudfront_distribution` |
| "WhatsApp deep-link + Google Maps embed" | "WhatsApp deep-link (`wa.me/`, rendered + in JSON-LD)" — drop "Google Maps embed" or add it to future work | No `maps.google` / `<iframe>` anywhere in `templates/` or `renderer.py` |
| Out-of-scope "Mobile app (Phase 2)" | "Play Store release (out of scope) — Flutter demo build is in scope" | You list "Flutter UI App" in scope and "Mobile app" out of scope on the same slide |
| SDG 8 / SDG 10 blocks | Keep | Fine |

### Slide 4 — Architecture Overview (image `image5.png`) — **redraw**
This is the highest-risk slide. The diagram is a "target-state" architecture rendered as if it were the current build. Everything below is in the diagram but **not** in the repo:

| Diagram element | Reality | Fix |
|---|---|---|
| Client: Next.js / Vercel | `apps/web/**` — every file is 0 bytes | Replace with **Flutter** (`voicefront/`) |
| Client: React Native (Expo) | No Expo app in repo | Delete |
| WebRTC / Browser Audio API | No WebRTC code | Delete or label future |
| IndicLID (first 5s → language ID) | `language_detect.py` stub → `"en"` | Grey out / move to future lane |
| IndicXlit (transliteration) | Not implemented | Grey out |
| BERT Punctuation Restoration | Not implemented; `normalize.py` is regex only | Grey out |
| IndicBERT NER | `ner_model.py` is a regex shim and is **never called** in the extract path | Replace with "Groq Llama-3.3-70B JSON extraction" |
| "Llama-3.3-88B / Gemma-2-9B (via Ollama)" | Groq `llama-3.3-70b-versatile`; QA uses `llama-3.1-8b-instant` | Correct the model names and the host |
| "k-NN over 12 templates by category" | `select_template()` is a **passthrough** on `spec["category"]`; 5 categories | "Category → template selection (5 categories)" |
| PostgreSQL (P) + Redis (R) | No DB in compose; no driver in any requirements; demo is stateless | Grey out / future |
| AWS EC2 + GPU + ML | Inference is hosted Groq; no GPU provisioned | "Groq hosted inference API" |
| S3 Static Hosting + CloudFront CDN | S3 yes; no CloudFront resource | S3 solid, CloudFront dashed |
| "Live Storefront URL (<50 ms TTFB)" | Unmeasured | Delete the number |
| Validated Schema JSON | Real (`packages/schemas/entity_types.py` + JSON Schema draft-07) | Keep |
| Playwright headless + 400+ rule checks | Playwright yes; **18** rules | "18 constraints × 5 viewports" |

**Convention to adopt:** solid = implemented, dashed = designed/next semester. Put a legend on the slide. This single change converts the deck's biggest liability into a credibility win.

**Redraw spec (paste into draw.io / PowerPoint shapes):**
```
[Flutter App (EN) ] --prompt--> [NLP 8002: Groq Llama-3.3-70B + regex fallback]
      |                              --> [StorefrontSpec (Pydantic + JSON Schema)]
      |                                   --> [Layout 8003: category selector + palette
      |                                        + HTML shell + JSON-LD + wa.me]
      |                                   --> [QA 8004: Playwright + axe-core, 5 viewports,
      |                                        18 constraints]  (REPAIR: written, not wired)
      |                                   -.-> [Publish: S3 (code) -.-> CloudFront (designed)]
[ASR 8001: Groq Whisper-large-v3] --optional--> NLP          (Indic stack: next semester)
```

### Slide 5 — Self-Healing QA Pipeline (image `image4.png`) — **redraw**
- "Constraint Graph Validation — **400+** rules" → **"18 constraints: 11 WCAG 2.2 AA + 7 structural, × 5 viewports (320/375/768/1024/1440 px)"**. If you want to mention 400+, write "target-state 400+ (WCAG 2.2 test suite)" in small grey text.
- **SORT** block ("Scoring Model → Risk Score"): currently a pass-through whose output is computed and discarded (`routers/qa.py`). Mark as *designed*, or delete the block.
- **REPAIR**: `repair_engine.py` genuinely calls Groq (`llama-3.3-70b-versatile`) with a heuristic two-line fallback — but `/v1/qa/run` hardcodes `repaired_count: 0` and never calls it. Either **wire it this week** (≈30 min: call `repair_violations()`, re-run detect, return counts) and keep the slide, or label the block *implemented, not yet wired*.
- **FAISS Repair-Rule Search (cosine > 0.87)** and **CodeBERT embedding**: neither library is a dependency anywhere in the repo. Move both to the future-work slide.
- "every novel fix teaches the system" → **"the rule store is designed to grow with every accepted fix (next semester)"**.
- Keep the final flow line but add "(S3 code implemented; CloudFront designed)".

### Slide 6 — Software & Hardware Requirements
| Row | Change |
|---|---|
| ASR | Keep "Whisper-large-v3 (via Groq)". Delete "IndicLID, IndicXlit, BERT Punctuation Restoration" or mark *next semester*. |
| NLP/Schema | "IndicBERT (NER)" → **"Llama-3.3-70B JSON extraction (Groq) + regex fallback"**. Keep "JSON Schema v7 Validator" (draft-07 is in the repo; Pydantic does the enforcement). "Gemma-2-9B (via Ollama)" → **"Llama-3.1-8B-Instant (QA repair, Groq)"**. |
| Layout | "Jinja2 templating engine, k-NN classifier, TF-IDF embeddings" → **"Jinja2 templates (5 categories), category routing, parameterised HTML shell, Unsplash hero/product imagery"**. k-NN and TF-IDF do not exist. |
| QA/Publish | "Playwright (headless Chromium), FAISS, CodeBERT" → **"Playwright + axe-core, 18 JSON constraints, Groq LLM repair, boto3 (S3 + CloudFront API)"**. |
| Frontend | "Next.js (web, Vercel), Flutter" → **"Flutter (Android/Windows/macOS); Next.js dashboard scaffolded only"**. |
| Data & Runtime | "PostgreSQL, Redis · Python, Node.js & TypeScript" → **"Python 3.12, FastAPI, Docker Compose; PostgreSQL/Redis designed for next semester"**. |
| Hardware: "AWS EC2 + GPU instances" | **"Groq hosted inference (no GPU provisioned); 24-hour g4dn.xlarge rental only for the WER/F1 benchmark run"** — this also reconciles the budget slide. |
| Design choice box | Keep the reasoning, but change "(Groq, Ollama)" → "(Groq)" and "custom-trained" wording stays valid. |

### Slide 7 — Project Budget (image `image6.png`) — rebuild as native shapes
- **Chart axis labels are corrupted.** The SVG shows ticks reading `0`, `₹`, `500`, `0`, `1200` — the crore/thousand formatting broke on export. A projector will expose this.
- Rebuild the table and the bar chart as native PowerPoint objects (or a clean Excel chart pasted as a picture at ≥2000 px). Never ship a screenshot of a table you can type.
- Arithmetic check: `0 + 1,206 + 0 + 1,146 + 1,500 = 3,852` ✅. But the bars look like 0 / ~1,200 / ~500 / ~1,100 / ~1,400 — the "Hosting ₹0" bar should be zero-height; make the chart match the table exactly.
- "Allocation: Paid fallback for a 1-year domain name (aiming for $0 via GitHub Student Pack first)" — two contradictory plans in one cell. State the chosen one, with the fallback in the contingency box.
- "24-hour GPU rental (g4dn.xlarge)" contradicts the "no GPU" architecture. Add "benchmark-only" to the cell.
- Add an as-of date: **"Costs as of October 2026."**

### Slide 8 — Literature Review (5 papers)
- **"WC3" → "W3C"**.
- The "How You'll Use It" column is written to the team ("your baseline citation", "you'll use it", "that comparison is your actual empirical contribution"). Rewrite in report voice: **"Relevance to this work"**.
- Paper 1 row says "pair its published WER numbers with **your own test_wer.py retail-domain run**". `test_wer.py` does **not** compute WER — it posts a 44-byte dummy WAV and checks the response shape. Change to "planned WER benchmark (Chapter 4)".
- Paper 3 row: "Not a research paper, so there's nothing to critique" — fine in a planning doc, wrong on a slide. Delete the sentence.
- "Then present your added retrieval step as your own contribution" — this is internal advice, not slide content. Remove.

### Slide 9 — Duplicate of the Research Gap table
`slide9.xml` embeds **both** `image2.jpg` (full-page table) and `image3.png` (the same table, cropped) — the cropped copy overlays or sits beside the full one. Delete one. Also its page number reads **16** while slide 8 reads **11**.
Keep this slide — it is one of the strongest in the deck — but re-set it as native text unless you fix the images: it is a 4-column table that would take two minutes to retype.
- Fix "the one thing none of them do together" — grammar: "the one thing **none of them does**". 
- The gap statement at the bottom is good; keep it verbatim.

### Slides 10–11 — Reference list
- "**All 20 papers**" — `docs/papers/` has 21 files (`20_w3c2023_wcag_2_2` exists as both `.pdf` and `.html`). Say "20 references".
- Both slides print page **15**. Fix.
- "four are reassigned into Tables 1–4 above" — there is only **one** summary table (slide 9). Change to "four are summarised in the Research Gap table".
- "in original reading order" — the list runs 2025 → 2022, i.e. reverse-chronological, not reading order. Say "grouped by year".
- The audience-facing slide shows internal annotations ("— reassigned to Table 1 (Person A)"). Move those to speaker notes.
- Paper 18 is listed as "López-Gil" and also appears as Othman in the earlier list (slide 11) — check the numbering against `docs/papers/18.pdf` (the audit identified 18.pdf as **Othman et al., PETRA '23**). Right now the two reference slides disagree about what #18 is.

---

## 2. Global fixes

1. **Page numbers.** Current footers: 2, 3, 4, 5, 6, 11, 16, 15, 15. Renumber 1–N after you add/remove slides.
2. **Footer consistency.** Every slide should read `VOICEFRONT-STORE · B.E. Major Project · AY 20XX–XX`.
3. **Image resolution.** Slides 4, 5, 7, 9 are pasted screenshots ~1000 px wide; text will be unreadable on a projector. Re-export at ≥2000 px or rebuild as native shapes.
4. **Theme.** Slide 5 is dark-on-light while the rest of the deck is light-on-dark; slide 7 is a different (blue) theme. One theme for the deck.
5. **Two numbers, one meaning.** Pick one rule count (18 implemented / 50 MVP target / 400+ framework) and use it identically on slides 3, 4, 5 and 6.
6. **Claim discipline.** Add a tiny footnote convention on every architecture slide: `solid = built · dashed = designed`.

---

## 3. New slides to add (this is what the deck is missing)

| Position | Slide | Content |
|---|---|---|
| after 6 | **Implementation Status** | Table: service / endpoint / status (Implemented · Partial · Designed) / evidence. Today: NLP ✅, Layout ✅, QA detect ✅, QA repair 🟡 (unwired), ASR 🟡 (Groq + simulator), Publish 🟡 (S3 code, stubbed QA gate), Flutter 🟡 (ChatScreen wired; layout body-shape mismatch) |
| after 6 | **Live Demo / Screenshots** | One prompt → one rendered storefront → one QA report. 3 screenshots. Even if the demo is live, have this as fallback. |
| after 8 | **Evaluation Plan (target vs actual)** | WER, schema validity, WCAG violations per page, TTFB, repair latency. Mark measured vs target. **Do not** print the 94.7% chip from the Flutter mock UI as a result — it is hardcoded. |
| before last | **Future Scope — Next Semester** | Copy from §4 below. |

---

## 4. Ready-to-paste: "Future Scope — Next Semester" slide

**Title:** Future Scope — Semester 2

**Left column — Complete the self-healing loop**
1. **Wire REPAIR into `/v1/qa/run`** — apply patch → re-run DETECT → report `repaired_count` and repair latency.
2. **LEARN** — embed accepted patches with CodeBERT, store in FAISS (`IndexFlatIP`), retrieve by cosine ≥ 0.87 before calling the LLM.
3. **SORT** — rank rules by historical failure frequency so DETECT runs under a compute/time budget.
4. **Grow rule set** 18 → 50 → 400+ from the WCAG 2.2 test suite.

**Middle column — Real multilingual voice**
5. **Microphone capture** in Flutter (`record` + `permission_handler`) replacing the simulated transcript.
6. **Language identification** (IndicLID / Whisper LID) replacing the `→ "en"` stub.
7. **Indic normalisation**: IndicXlit transliteration, Devanagari-aware normalisation, punctuation restoration.
8. **Measure WER** on LAHAJA / Vistaar / IndicVoices subsets per language; publish per-language WER.

**Right column — Production hardening**
9. **Persistence**: PostgreSQL (specs, versions, QA reports) + Redis (task state); status enum `PENDING → … → PUBLISHED`.
10. **Publishing**: Terraform `aws_cloudfront_distribution`, IAM deploy role, ACM certificate, custom domain; server-side QA re-check before upload.
11. **Evaluation suite**: WER, schema F1, axe WCAG pass-rate, Lighthouse CI (CWV), TTL stopwatch.
12. **10+ Indian languages**; ONDC / UPI deep-link integration.

**Footer line:** "Semester 1 delivered an English prompt→storefront pipeline with detect-and-report QA; Semester 2 closes the repair loop, restores multilingual voice, and takes publishing live."

---

## 5. Pre-submission checklist

- [ ] Slide 4 redrawn; every box either built or dashed
- [ ] One rule count used everywhere (18 implemented / 50 target / 400+ framework)
- [ ] Slide 5: REPAIR either wired or labelled
- [ ] Slide 6 model names match `schema_builder.py` and `repair_engine.py`
- [ ] Slide 3: maps embed removed; Hindi ASR removed from "in scope"
- [ ] Slide 7 rebuilt natively; chart matches table; as-of date added
- [ ] Slide 8 "WC3" → "W3C"; coaching text removed
- [ ] Slide 9 duplicate image removed
- [ ] Reference count and #18 resolved
- [ ] Page numbers 1–N; footers identical
- [ ] AY consistent across deck, report, certificate
- [ ] New: status slide, demo slide, evaluation slide, future-scope slide
- [ ] Re-export PDF from the corrected PPT; check the PDF, not just the editor
