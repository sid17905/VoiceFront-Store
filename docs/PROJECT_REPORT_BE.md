# B.E. Major Project Report — VoiceFront-Store

> **How to use this file.** This is the full report draft in the section order of `B.E.-Project-Report-25-26.docx`. Paste each section into the .docx under the matching heading, then apply the template's styles: chapter titles 16 pt Times New Roman Bold Centred; section headings 14 pt Bold; body 12 pt Times New Roman, justified, 1.5 line spacing; figures centred with captions below; tables captioned above. Delete the bracketed editorial notes (they start with **NOTE:**). Replace every `⟨…⟩` placeholder.

---

## Title Page

**A VOICE-TO-STOREFRONT PLATFORM WITH AUTOMATED ACCESSIBILITY QA AND LLM-ASSISTED REPAIR**

Submitted in partial fulfilment of the requirement of University of Mumbai for the Degree of

**Bachelor of Engineering in Artificial Intelligence and Data Science**

**Submitted By**

| Name | Roll No. |
|---|---|
| Siddhesh Gangurde | 20 |
| Dhiren Achrekar | 01 |
| Sarvesh Dhanrale | 16 |
| Aayush Tanwar | 64 |

**Supervisor:** Dr. Sunil Chavan

Department of Artificial Intelligence and Data Science
Smt. Indira Gandhi College of Engineering, Ghansoli — 400701
(An Autonomous Institute)
Academic Year 2026–27

**NOTE:** the supplied template (`T.E.-Project-Report-25-26.docx`) is a **T.E. / minor-project** template: its certificate reads "SE Mini Project" and its title page reads "Academic Year 2025 – 26". This draft is written for **B.E. Major Project, AY 2026–27**. Before printing, edit the template's certificate, title page, approval page and declaration to match this draft — do not copy the template's "SE"/"T.E." wording back in.

---

## Certificate

This is to certify that the requirements for the B.E. Major Project report entitled **"Voice-to-Storefront Platform with Automated Accessibility QA and LLM-Assisted Repair"** have been successfully completed by the following students of Bachelor of Engineering in Artificial Intelligence and Data Science, Smt. Indira Gandhi College of Engineering, Ghansoli (An Autonomous Institute), during the academic year 2026–27.

| Name | Roll No. |
|---|---|
| Siddhesh Gangurde | 20 |
| Dhiren Ackrekar | 01 |
| Sarvesh Dhanrale | 16 |
| Aayush Tanwar | 64 |

in partial fulfilment of the requirements for the degree of Bachelor of Engineering.

**Dr. Sunil Chavan** — Project Guide

Department of Artificial Intelligence and Data Science
SMT. INDIRA GANDHI COLLEGE OF ENGINEERING
GHANSOLI — 400701 (An Autonomous Institute)

---

## Report Approval

This B.E. Major Project report entitled **"Voice-to-Storefront Platform with Automated Accessibility QA and LLM-Assisted Repair"** by Siddhesh Gangurde, Dhiren Achrekar, Sarvesh Dhanrale, and Aayush Tanwar is approved for the degree of Bachelor of Engineering in Artificial Intelligence and Data Science, Smt. Indira Gandhi College of Engineering, Ghansoli (An Autonomous Institute).

**Examiners:**
1. ______________________
2. ______________________

**Supervisors:**
1. ______________________
2. ______________________

Date: ____________  Place: Ghansoli

---

## Declaration

We declare that this written submission for the B.E. Major Project report entitled **"Voice-to-Storefront Platform with Automated Accessibility QA and LLM-Assisted Repair"** represents our ideas in our own words and where others' ideas or words have been included, we have adequately cited and referenced the original sources. We also declare that we have adhered to all principles of academic honesty and integrity and have not misrepresented or fabricated or falsified any idea/data/fact/source in our submission. We understand that any violation of the above will be cause for disciplinary action by the Institute and can also evoke penal action from the sources which have thus not been properly cited or from whom proper permission has not been taken when needed.

| Name | Roll No. | Signature |
|---|---|---|
| Siddhesh Gangurde | 20 | |
| Dhiren Achrekar | 01 | |
| Sarvesh Dhanrale | 16 | |
| Aayush Tanwar | 64 | |

Date: ____________  Place: Ghansoli

---

## Table of Contents

> Build this in Word with References → Table of Contents after applying Heading 1/2/3 styles to the chapters below. Structure to expect:

```
Abstract ........................................................ i
List of Figures ............................................... ii
List of Tables ................................................ iii
Chapter 1  Introduction ........................................ 1
   1.1  Background and Motivation
   1.2  Problem Statement
   1.3  Objectives
   1.4  Scope of the Project
   1.5  Organisation of the Report
Chapter 2  Literature Survey ................................... 4
   2.1  Literature Summary
   2.2  Research Gap
Chapter 3  Proposed System .................................... 8
   3.1  System Architecture
   3.2  End-to-End Data Flow
   3.3  Data Model — StorefrontSpec
   3.4  Module Description
   3.5  Algorithms
   3.6  Software Requirements Specification
   3.7  Hardware and Software Requirements
   3.8  Dataset and Evaluation Metrics
Chapter 4  Performance and Results ............................ 16
   4.1  Experimental Setup
   4.2  Functional Results
   4.3  Quantitative Results
   4.4  Qualitative Analysis
   4.5  Discussion and Limitations
Chapter 5  Applications ....................................... 22
Chapter 6  Conclusion and Future Scope ........................ 24
References .................................................... 27
Acknowledgement ............................................... 29
```

---

## Abstract

Small retailers in India remain largely absent from the digital marketplace, not for lack of connectivity but for lack of usable tools: existing website builders assume coding fluency and hours of manual content entry. This project designs, implements and evaluates **VoiceFront-Store**, a five-stage pipeline that converts a spoken or typed shop description into a complete, accessible, mobile-first storefront. The pipeline comprises an automatic speech recognition stage (Whisper-large-v3, hosted), a natural-language understanding stage that converts free text into a validated `StorefrontSpec` using a large language model with a rule-based fallback, a layout synthesis stage that renders category-specific HTML with structured data (JSON-LD) and a WhatsApp ordering link, a quality-assurance stage that renders the page in headless Chromium and checks it against accessibility and structural constraints at five viewport widths, and a publishing stage that uploads the verified bundle to object storage and invalidates a CDN. Implemented as five independent FastAPI services with a shared Pydantic schema and a Flutter client, the system currently supports five retail categories, eighteen quality constraints, and an English-language interaction path. Evaluation covers extraction validity, rendering correctness across categories, and accessibility violation detection; multilingual voice input, retrieval-based repair learning, and live CDN publication are identified as the immediate next-semester extensions.

**NOTE:** 12–15 lines as the template asks; this is ~190 words, trim or keep depending on the department's limit.

---

## List of Figures

| Figure | Title |
|---|---|
| Figure 1.1 | The digital divide in Indian micro-retail ⟨optional; a chart of the statistics you cite⟩ |
| Figure 3.1 | Five-stage system architecture |
| Figure 3.2 | End-to-end sequence: prompt → spec → page → QA report |
| Figure 3.3 | `StorefrontSpec` entity relationship |
| Figure 3.4 | Self-healing QA loop (Detect → Repair, with Sort/Learn as future work) |
| Figure 3.5 | Flutter application screens (chat, preview, QA report) |
| Figure 4.1 | Generated storefront — food category |
| Figure 4.2 | Generated storefront — electronics category |
| Figure 4.3 | QA report for the seeded defective fixture |
| Figure 4.4 | Accessibility violations by severity across categories |

## List of Tables

| Table | Title |
|---|---|
| Table 2.1 | Summary of literature survey |
| Table 2.2 | Research gap matrix |
| Table 3.1 | `StorefrontSpec` field specification |
| Table 3.2 | QA constraint inventory |
| Table 3.3 | Functional requirements |
| Table 3.4 | Non-functional requirements |
| Table 3.5 | Hardware and software requirements |
| Table 4.1 | Extraction results on the scripted prompt set |
| Table 4.2 | Rendering results across five categories |
| Table 4.3 | Accessibility violations detected per fixture |
| Table 4.4 | Target versus measured performance |

---

# Chapter 1 — Introduction

This chapter introduces the domain, states the problem, lists the objectives, defines scope, and outlines the report.

## 1.1 Background and Motivation

India's retail sector is dominated by small, owner-operated stores. While broadband and smartphone penetration have grown substantially in Tier-2 and Tier-3 cities, the proportion of these retailers with any digital storefront remains low. The barrier is not connectivity but **interface**: current website builders require the owner to choose layouts, write copy, source images, and navigate content-management systems. Most shop owners have neither the time nor the training for this.

Large language models and hosted speech-recognition APIs have, within the last three years, made it feasible to accept a natural-language description — "a bakery in Bandra selling sourdough at ₹180, open 8 to 8, WhatsApp 98765 43210" — and derive a structured representation of a business from it. The remaining problem is not understanding the sentence but producing a **deployable artefact**: a page that carries correct structured data, works on a phone, and is accessible.

> **NOTE:** replace the two statistics in this paragraph with cited ones (TRAI for broadband; a verified MSME/kirana count — **do not** use "340 million micro-retailers", which is not a defensible figure for India; the commonly cited numbers are ~13 M kirana stores and ~63 M MSMEs).

## 1.2 Problem Statement

Given a short, informal, possibly spoken description of a shop, produce a complete and accessible storefront web page and a publishing-ready bundle, without requiring the shop owner to make any design or coding decision.

Formally: given an utterance or prompt *P* describing a business, generate *S = Spec(P)*, a validated structured specification, and *H = Render(S)*, an HTML document, such that *H* satisfies (i) content fidelity to *P*, (ii) the accessibility constraints in the project's constraint set, and (iii) responsive rendering at viewport widths from 320 px to 1440 px. The system must also report which constraints *H* violates, and — where possible — repair them.

## 1.3 Objectives

The objectives of this work are:

1. To implement a speech-to-text stage for shop descriptions using a hosted Whisper-large-v3 model, with a defensive fallback when the inference API is unavailable.
2. To study and implement schema-constrained information extraction: convert free text into a validated `StorefrontSpec` using an LLM with JSON-mode output, a bounded self-correction loop, and a deterministic rule-based fallback.
3. To build a layout synthesis stage that selects a category-appropriate template and palette and emits HTML containing structured data (schema.org JSON-LD) and a WhatsApp deep link.
4. To implement an automated quality-assurance stage that renders the page in headless Chromium at five viewport widths and evaluates accessibility and structural constraints using axe-core and custom checks.
5. To implement an LLM-assisted repair stage that proposes patches for detected violations, and to evaluate its effect on the violation count.
6. To evaluate the pipeline on a scripted prompt set across five retail categories, reporting extraction validity, rendering correctness, and violation counts.

> **NOTE:** objective 5 is only achievable if you wire `repair_engine.py` into `/v1/qa/run` (see §4.5). If not wired by submission, reword to "to design and implement the repair stage and evaluate it in isolation."

## 1.4 Scope of the Project

**In scope (this semester):** English text or voice input; five retail categories (food, apparel, electronics, pharmacy, services); a validated shared schema; category-based layout synthesis; automated accessibility and structural QA at five viewport widths; LLM-assisted repair of detected violations; S3-based publishing code; a Flutter client.

**Out of scope (next semester):** full multilingual voice input (Hindi, Marathi and additional Indian languages); the learned repair-rule store; production CDN deployment and custom-domain automation; order processing and payment integration; persistent multi-tenant storage.

## 1.5 Organisation of the Report

Chapter 2 reviews the literature on speech recognition for Indian languages, LLM-based information extraction, automated website generation, and automated accessibility repair, and identifies the gap this work addresses. Chapter 3 presents the proposed system: architecture, data model, modules, algorithms, and requirements. Chapter 4 reports performance and results. Chapter 5 discusses applications. Chapter 6 concludes and sets out future scope.

---

# Chapter 2 — Literature Survey

## 2.1 Literature Summary

**Table 2.1 — Summary of the literature survey**

| SN | Author(s) / Year | Method | Contribution | Limitation |
|---|---|---|---|---|
| 1 | Radford et al. (2022) — *Robust Speech Recognition via Large-Scale Weak Supervision* | Whisper; 680k hours of weakly supervised multilingual audio | Strong zero-shot ASR across languages and accents without fine-tuning | Indic languages under-represented in training mix; no retail-domain vocabulary; code-switching weak |
| 2 | Javed et al. (2024) — *LAHAJA* | Multi-accent Hindi ASR benchmark | Quantifies accent-related degradation in Hindi ASR | Evaluation-only; no pipeline integration |
| 3 | Javed et al. (2024) — *IndicVoices* | Large multilingual Indian speech corpus | Provides training/eval data for Indic ASR | Dataset contribution; not a storefront system |
| 4 | Wang et al. (2023) — *GPT-NER* | Prompt an LLM to perform NER as generation | LLM NER competitive with supervised models | Evaluated on news/Wikipedia, not commerce; self-checking adds latency and cost |
| 5 | Willard & Louf (2023) — *Efficient Guided Generation* | Constrained decoding via finite-state machines | Guarantees schema-conformant JSON output | Requires logit access; unavailable with hosted black-box APIs |
| 6 | Calò & De Russis (2023) — *Leveraging LLMs for End-User Website Generation* | Plain-language description → LLM-generated site | Closest prior work to this project | Small study; no voice input; no multilingual support |
| 7 | Si et al. (2025) — *Design2Code* | Benchmark of multimodal code generation for front-end engineering | Establishes metrics for generated-UI fidelity | Screenshot-to-code setting; no accessibility objective |
| 8 | Huang et al. (2024) — *ACCESS* | Prompt-engineered LLM repair of web accessibility violations | Shows LLM repair is viable against WCAG checks | No retrieval of prior successful fixes; one-shot repair |
| 9 | Wang et al. (2023) — *RAP-Gen* | Retrieval-augmented patch generation with CodeT5 | Retrieval of similar past patches improves repair | General program repair; not accessibility-specific |
| 10 | Othman et al. (2023) — PETRA '23 | ChatGPT for automatic WCAG remediation vs manual testing | Demonstrates LLM remediation of accessibility defects | WCAG 2.1; no systematic evaluation loop |
| 11 | López-Gil & Pereira (2024) | Turning manual accessibility success criteria into automatic checks | Bridges WCAG criteria to automatable tests | Grounds the constraint design; not a generation system |
| 12 | W3C (2023) — *WCAG 2.2* | Normative accessibility standard | Defines the conformance target for this work | Specification, not a technique |

> **NOTE:** the deck also cites Ge et al. (2025), Fithian & Skobelev (2025), Laurençon et al. (2024), Gur et al. (2023), Zhang et al. (2024) and van de Ven et al. (2024). Add them if the department expects ~20 entries — keep the table to 12–15 rows and put the rest in the reference list, or split into Table 2.1 (speech/NLP) and Table 2.2 (layout/QA) as the template's four-table structure suggests.

## 2.2 Research Gap

**Table 2.2 — Research gap matrix**

| Capability | Whisper (2022) | GPT-NER (2023) | Calò & De Russis (2023) | ACCESS / RAP-Gen (2023–24) | **This work** |
|---|---|---|---|---|---|
| Voice / speech input | ✔ (ASR only) | — | — | — | ✔ |
| Domain-constrained extraction | — | partial | — | — | ✔ |
| Automated page generation | — | — | ✔ | — | ✔ |
| Accessibility checking | — | — | — | ✔ | ✔ |
| Automated repair | — | — | — | ✔ | ✔ (LLM-assisted) |
| Learned reuse of repairs | — | — | — | partial (RAP-Gen) | designed (next semester) |
| Indian-language support | partial | — | — | — | next semester |

**The gap:** no existing system joins speech input, schema-constrained extraction, template-based generation, and automated accessibility checking and repair in a single pipeline aimed at low-literacy micro-retailers. Each prior work solves exactly one of these four problems.

---

# Chapter 3 — Proposed System

## 3.1 System Architecture

The system is decomposed into five independently deployable FastAPI services, plus a Flutter client, communicating over HTTP/JSON through a shared schema package.

**Figure 3.1 — Five-stage system architecture.** ⟨Insert the redrawn architecture diagram from the deck — the solid/dashed version — not the old one.⟩

| Stage | Service | Port | Responsibility | Implementation status |
|---|---|---|---|---|
| 1. Speech input | `asr-service` | 8001 | Validate audio, transcribe (Whisper-large-v3 via hosted API), normalise text | Implemented, with simulator fallback; English-only |
| 2. Understanding | `nlp-service` | 8002 | Text → validated `StorefrontSpec` (LLM with JSON mode + regex fallback) | Implemented |
| 3. Layout synthesis | `layout-service` | 8003 | Category → palette + HTML, JSON-LD, WhatsApp link; reference-site scraping endpoint | Implemented |
| 4. Quality assurance | `qa-service` | 8004 | Multi-viewport render; axe-core + custom constraint checks; LLM repair (written) | Detect implemented; repair implemented but not on the request path |
| 5. Publishing | `publish-service` | — | Upload bundle to S3, create CloudFront invalidation, return URL | S3/CloudFront code implemented; QA gate stubbed |

Supporting packages: `packages/schemas` (Pydantic models, JSON Schema draft-07, TypeScript mirror) and `packages/common_utils` (error hierarchy, database and auth helpers).

## 3.2 End-to-End Data Flow

**Figure 3.2 — End-to-end sequence.** ⟨Include a sequence diagram for the demo path: Flutter/HTTP client → NLP → Layout → QA → (Publish).⟩

1. The client sends a prompt (typed, or a transcript from Stage 1) to `POST /v1/nlp/extract`.
2. The NLP service builds a system prompt containing the target schema, calls the LLM in JSON mode, validates the response with Pydantic, and if invalid re-prompts with the validation errors (at most two rounds). If the API is unavailable, a deterministic regex extractor is used.
3. The returned `StorefrontSpec` is posted to `POST /v1/layout/generate`.
4. The layout service selects a palette and a template for the category, renders HTML containing schema.org JSON-LD and a `wa.me/<number>` ordering link, and returns it inline.
5. The HTML is posted (by version) to `POST /v1/qa/run`; the QA service renders it in headless Chromium at five widths and evaluates the constraint set.
6. A passing bundle is posted to `POST /v1/publish`, which uploads to S3 and returns the public URL after a CloudFront invalidation completes.

## 3.3 Data Model — StorefrontSpec

The schema is defined once in `packages/schemas/entity_types.py` (Pydantic) and mirrored as JSON Schema draft-07 and TypeScript.

**Table 3.1 — `StorefrontSpec` field specification**

| Field | Type | Required | Notes |
|---|---|---|---|
| `shop_name` | string (min length 1) | **yes** | |
| `category` | enum | **yes** | `food \| apparel \| electronics \| pharmacy \| services` |
| `description` | string | no | Free-text tagline |
| `products[]` | list of `ProductItem` | no | `name`, `price` (number, string or null), `currency` (default INR), `description`, `image_url` |
| `hours[]` | list | no | Opening hours as structured entries |
| `location` | `LocationInfo` | no | `address`, `city`, `state`, `pincode`, `lat`, `lng` |
| `contact` | `ContactInfo` | no | `phone`, `whatsapp`, `email`, `instagram` |

> **NOTE:** the submitted project contract (`docs/procedure/data.md`) made `products`, `contact.whatsapp` and numeric `price` mandatory. The operative schema relaxes this so that partial descriptions still render. State this explicitly as a **schema revision (v1.1)** in the report — do not let the panel discover the discrepancy.

## 3.4 Module Description

**3.4.1 ASR module.** Accepts multipart audio, validates MIME type and extension, calls the hosted Whisper-large-v3 endpoint with `verbose_json` output, and post-processes whitespace, currency and phone formats. If no API key is configured or the call fails, it returns a canned transcript so that downstream stages remain testable. Language identification is currently fixed to English behind a pluggable interface.

**3.4.2 NLP module.** Constructs a schema-carrying system prompt, calls the model with `response_format: json_object` at temperature 0.1, parses and validates the response, and retries with the validation errors appended on failure. A regex fallback extracts shop name, category keywords, Indian phone numbers and prices, and fills defaults for missing fields.

**3.4.3 Layout module.** Selects a palette by category, builds a mobile-first HTML document with hero imagery, product cards, hours, location and a sticky WhatsApp call-to-action, and emits schema.org JSON-LD. A separate scraping endpoint drives headless Chromium against a reference URL to extract a component's computed CSS, HTML and a highlighted screenshot, which supports the component-library workflow.

**3.4.4 QA module.** Loads JSON constraint definitions, renders the bundle in headless Chromium at 320, 375, 768, 1024 and 1440 px, injects axe-core, and maps axe rule IDs to project rule IDs. Custom JavaScript checks cover horizontal overflow, broken images, duplicate IDs, empty links, missing viewport meta, focus-outline removal, and tap-target size. Output is a structured report with severity levels `critical`, `major`, `minor`.

**3.4.5 Repair module.** For each violation, calls the LLM with the rule description and the offending HTML and returns a patched snippet; when no key is available, a two-line heuristic substitutes a default `alt` and a contact anchor. The repair stage is implemented as a library function and is being integrated into the QA request path.

**3.4.6 Publish module.** Uploads `storefronts/<version_id>/index.html` to S3 via boto3, relies on a bucket policy for public read, creates a CloudFront invalidation, and polls until completion before returning a URL — failing closed on timeout.

**3.4.7 Client.** A Flutter application with a conversational entry point: the owner describes or edits the shop in natural language, the app calls the NLP and layout endpoints, and the result is shown in a preview surface with a QA summary.

## 3.5 Algorithms

**Algorithm 1 — Schema-constrained extraction with self-correction**
```
INPUT: prompt P, schema S, max_rounds = 2
spec ← LLM_extract(P, S)                    # JSON mode, temperature 0.1
for round in 1..max_rounds:
    errors ← validate(spec, S)               # Pydantic
    if errors is empty: return (spec, valid)
    spec ← LLM_extract(P, S, prior=spec, errors=errors)
return (regex_fallback(P), partial)
```

**Algorithm 2 — Multi-viewport constraint evaluation**
```
INPUT: html H, rules R, viewports V = [320,375,768,1024,1440]
violations ← ∅
for width in V:
    page ← chromium.render(H, width)
    violations ← violations ∪ axe_core(page, R ∩ axe_rules)
    violations ← violations ∪ custom_checks(page, R ∩ custom_rules)
return deduplicate(violations), severity_sort(violations)
```

**Algorithm 3 — Repair and re-verify** *(implemented, not yet on the request path)*
```
INPUT: violations X, html H
for v in X:
    patch ← LLM_repair(v.rule, v.context(H))  or  heuristic_patch(v)
    H ← apply(H, patch)
X' ← evaluate(H)
return H, repaired_count = |X| − |X'|
```

## 3.6 Software Requirements Specification

**Table 3.3 — Functional requirements**

| ID | Requirement |
|---|---|
| FR-1 | The system shall accept a text prompt or an audio file and produce a storefront specification. |
| FR-2 | The system shall validate the specification against the shared schema and report invalid fields. |
| FR-3 | The system shall render a storefront page for each of the five categories. |
| FR-4 | The rendered page shall contain the shop name, products with prices, opening hours, location, a WhatsApp ordering link, and schema.org JSON-LD. |
| FR-5 | The system shall render the page at five viewport widths and report accessibility and structural violations. |
| FR-6 | The system shall classify each violation by severity. |
| FR-7 | The system shall propose and apply repairs for detected violations. |
| FR-8 | The system shall publish a passing bundle to object storage and return a URL. |
| FR-9 | The client shall display the generated page and the QA summary. |

**Table 3.4 — Non-functional requirements**

| ID | Requirement |
|---|---|
| NFR-1 | End-to-end generation for one prompt shall complete within a practical interactive time (target: < 10 minutes; measured value in Table 4.4). |
| NFR-2 | The system shall remain usable when the LLM API is unavailable, via the deterministic fallback. |
| NFR-3 | Services shall be independently deployable and expose health endpoints. |
| NFR-4 | The shared schema shall have a single source of truth across Python and TypeScript. |
| NFR-5 | The system shall not publish a bundle that failed QA. |

## 3.7 Hardware and Software Requirements

**Table 3.5 — Hardware and software requirements**

| Component | Specification |
|---|---|
| Development machine | Windows 11 / macOS; 16 GB RAM; 20 GB free disk; RTX-class GPU not required for the runtime path |
| Runtime | Python 3.12, Node.js 20+, Flutter 3.x |
| Frameworks | FastAPI, Uvicorn, Pydantic v2, Jinja2, Playwright (Chromium), axe-core, boto3 |
| Inference | Hosted API (Whisper-large-v3, Llama-3.3-70B) — no local GPU provisioning |
| Containerisation | Docker Compose (asr 8001, nlp 8002, layout 8003, qa 8004) |
| Storage | S3 bucket + bucket policy; CloudFront distribution (designed) |

## 3.8 Dataset and Evaluation Metrics

**Prompts.** A scripted set of English prompts spanning the five categories, each containing a shop name, at least three products with prices, opening hours, a WhatsApp number and a locality. A sixth, deliberately defective fixture is used for QA.

**Metrics.**
- *Extraction:* schema-validity rate (fraction of prompts yielding a valid specification), and field-level accuracy against manually annotated ground truth (shop name, category, product count, price correctness).
- *Rendering:* fraction of categories whose output contains all required elements (name, products, prices, `wa.me` link, viewport meta, correct JSON-LD type).
- *QA:* number of violations detected per fixture, by severity and by viewport; agreement with axe-core's native output.
- *Repair (if wired):* violations before vs after repair, repair success rate, mean repair latency.
- *Latency:* wall-clock time per stage and end to end.

> **NOTE:** do **not** report WER or schema F1 as measured. The files named `test_wer.py` and `test_schema_f1.py` currently exercise endpoints with dummy input; they do not compute those metrics. Either build the benchmarks (Chapter 6, item 11) or report them as target-only.

---

# Chapter 4 — Performance and Results

## 4.1 Experimental Setup

⟨Describe the machine used, the Docker Compose stack, whether a hosted-API key was configured, and the date of the runs. Include both modes: **keyed** (LLM + Whisper live) and **offline** (fallbacks), because the fallback path is a designed feature and should be reported, not hidden.⟩

## 4.2 Functional Results

**Figure 4.1 — Generated storefront, food category.** ⟨Screenshot of a real render.⟩
The food prompt produced a page containing the shop name, all three products with prices, opening hours, locality, a WhatsApp deep link and `LocalBusiness` JSON-LD, correctly rendered at 375 px and 1440 px.

**Figure 4.2 — Generated storefront, electronics category.** ⟨Screenshot.⟩
⟨Repeat for apparel, pharmacy, services, or state that all five were verified by `test_all_categories.py`.⟩

**Table 4.1 — Extraction results on the scripted prompt set**

| Prompt | Category (expected) | Category (extracted) | Valid? | Products extracted / expected | Notes |
|---|---|---|---|---|---|
| S1 Food | food | | | /3 | |
| S2 Electronics | electronics | | | /3 | |
| S3 Services | services | | | /3 | |
| S4 Apparel | apparel | | | /3 | |
| S5 Pharmacy | pharmacy | | | /3 | |
| S6 Empty prompt | — | — | HTTP 400 `EMPTY_PROMPT` | — | Negative test |

**Table 4.2 — Rendering results across five categories**

| Category | Shop name | Products + prices | `wa.me` link | Viewport meta | JSON-LD type | Result |
|---|---|---|---|---|---|---|
| food | | | | | LocalBusiness | |
| electronics | | | | | Store | |
| apparel | | | | | Store | |
| pharmacy | | | | | Store | |
| services | | | | | ProfessionalService | |

> **NOTE:** fill the JSON-LD type column from `renderer.py` — use the actual `@type` emitted, not an assumption.

## 4.3 Quantitative Results

**Table 4.3 — Accessibility violations detected per fixture**

| Fixture | Critical | Major | Minor | Total | Viewports affected |
|---|---|---|---|---|---|
| `fixture-bad.html` | | | | ⟨expected ≈ 6–7⟩ | |
| `fixture-good.html` | | | | ⟨expected ≈ 0⟩ | |
| Generated page (S1) | | | | | |

**Figure 4.3 — QA report for the defective fixture.** ⟨Screenshot of the structured report.⟩

**Table 4.4 — Target versus measured performance**

| Metric | Target | Measured | Status |
|---|---|---|---|
| Extraction validity rate | 5/5 prompts valid | ⟨fill⟩ | |
| Rendering completeness | 5/5 categories complete | ⟨fill⟩ | |
| Accessibility violations, defective fixture | > 0 detected | ⟨fill⟩ | |
| Accessibility violations, good fixture | 0 | ⟨fill⟩ | |
| End-to-end generation time | < 10 min | ⟨fill⟩ | |
| Repair: violations reduced | improvement > 0 | ⟨fill only if wired⟩ | |
| WER (English, retail prompts) | report per language | not measured | next semester |
| Schema F1 vs ground truth | report | not measured | next semester |
| Lighthouse / Core Web Vitals | ≥ 90 performance | not measured | next semester |

**Be explicit in the text:** every "not measured" row is a stated limitation, not an omission. A panel accepts a named gap; it does not accept a target quoted as a result.

## 4.4 Qualitative Analysis

⟨Discuss: which categories extract well and why (vocabulary overlap with the prompt), where the regex fallback degrades (it invents a "Signature Item" and a default Mumbai address when products are absent — this is a real failure mode worth reporting), and which violations the LLM repair fixes reliably (alt text, empty links) versus poorly (contrast, tap-target sizing).⟩

## 4.5 Discussion and Limitations

1. **Repair is implemented but not yet on the request path** — `/v1/qa/run` reports `repaired_count: 0`. Wiring it is a small change and is the first item of future work.
2. **The learned repair store (FAISS/CodeBERT) is designed, not built.** No retrieval dependency exists in the codebase.
3. **Multilingual voice is deferred.** Language identification returns English; no Indic normalisation or transliteration is implemented.
4. **Publishing is partially live.** S3 upload and invalidation code is complete; the server-side QA re-check is stubbed and the CloudFront resource is not yet declared in Terraform.
5. **Rendering currently shares one page shell across categories**, parameterised by palette, rather than rendering the per-category templates. This is a fidelity limitation to state plainly.

---

# Chapter 5 — Applications

1. **Micro-retail storefronts.** Kirana, bakery, apparel, electronics, pharmacy and service businesses can obtain a mobile-first page with WhatsApp ordering in a single interaction.
2. **ONDC seller onboarding.** Generated structured data and product listings reduce the manual effort of onboarding small sellers to open commerce networks.
3. **Assistive and low-literacy interfaces.** The voice-first path supports owners who are uncomfortable typing; the accessibility checking ensures the *output* is usable by customers with disabilities.
4. **Accessibility remediation as a service.** The QA stage is independently useful: given any HTML bundle, it reports WCAG 2.2 AA and structural violations across five viewports.
5. **Template and design-system research.** The component-library and reference-scraping tooling support studying how real commercial sites structure nav, hero, product-grid and contact sections.
6. **Educational use.** The five-service decomposition is a practical teaching example of schema-first microservice design with LLM integration and deterministic fallbacks.

---

# Chapter 6 — Conclusion and Future Scope

## 6.1 Conclusion

This project designed and implemented VoiceFront-Store, a five-stage pipeline that converts a shop description into a mobile-first, accessible storefront. The work delivers: a shared, validated `StorefrontSpec` schema as the contract between services; an LLM-based extraction stage with a deterministic fallback that keeps the system usable without network access; a layout stage that renders five retail categories with structured data and a WhatsApp ordering path; and a QA stage that renders pages in a real browser at five viewport widths and reports accessibility and structural violations against an eighteen-constraint rule set. The pipeline is containerised, health-checked, and exercised end to end. The project also establishes the boundaries of what is complete: repair is implemented but not yet integrated, the learned repair store and multilingual voice are designed and deferred, and publishing is complete at the storage layer but not yet at the CDN layer. These are stated as scope decisions, not concealed.

## 6.2 Future Scope

**Completing the self-healing loop.**
1. Integrate the repair stage into `/v1/qa/run`: apply the patch, re-run detection, and report the repaired count and repair latency.
2. Implement the learning stage: embed accepted patches with CodeBERT, store them in a FAISS index, and retrieve by cosine similarity before invoking the LLM.
3. Implement rule ranking (risk scoring) so detection runs under a compute budget.
4. Expand the constraint set from 18 to the 50-constraint MVP target and toward the 400+ target-state set drawn from the WCAG 2.2 test suite.

**Restoring multilingual voice.**
5. Replace the simulated transcript in the client with real microphone capture and audio upload.
6. Implement language identification (IndicLID or Whisper language detection) in place of the fixed-English stub.
7. Add Indic normalisation: transliteration (IndicXlit), Devanagari handling, and punctuation restoration.
8. Measure word error rate per language on the LAHAJA, Vistaar and IndicVoices benchmark subsets, and publish per-language results.

**Production hardening.**
9. Add persistence: PostgreSQL for specifications, versions and QA reports; Redis for task state and the status lifecycle.
10. Complete publishing: declare the CloudFront distribution in Terraform, add an IAM deploy role and ACM certificate, support custom domains, and enforce the server-side QA re-check before upload.
11. Build the evaluation suite: WER, schema F1 against annotated ground truth, axe WCAG pass rate, Lighthouse CI for Core Web Vitals, and a time-to-live stopwatch.
12. Extend to ten or more Indian languages and integrate ONDC and UPI payment deep links.

The semester-1 contribution is an English prompt-to-storefront pipeline with detect-and-report quality assurance; semester 2 closes the repair loop, restores multilingual voice, and takes publishing live.

---

## References

> **NOTE:** IEEE numeric style, ordered by first citation. These 20 entries match `docs/papers/`. Verify each DOI/arXiv ID before submission — the deck currently lists #18 two different ways.

[1] A. Radford, J. W. Kim, T. Xu, G. Brockman, C. McLeavey, and I. Sutskever, "Robust Speech Recognition via Large-Scale Weak Supervision," arXiv:2212.04356, 2022.

[2] K. S. Bhogale, A. Raman, T. Javed, S. Doddapaneni, A. Kunchukuttan, P. Kumar, and M. M. Khapra, "Vistaar: Diverse Benchmarks and Training Sets for Indian Language ASR," in *Proc. Interspeech*, 2023.

[3] T. Javed, S. Doddapaneni, A. Raman, K. S. Bhogale, G. Ramesh, A. Kunchukuttan, P. Kumar, and M. M. Khapra, "Towards Building ASR Systems for the Next Billion Users," in *Proc. AAAI*, 2022.

[4] T. Javed, J. Nawale, S. Joshi, E. George, K. Bhogale, D. Mehendale, and M. M. Khapra, "LAHAJA: A Robust Multi-accent Benchmark for Evaluating Hindi ASR Systems," in *Proc. Interspeech*, 2024. arXiv:2408.11440.

[5] S. Wang, X. Sun, X. Li, R. Ouyang, F. Wu, T. Zhang, J. Li, and G. Wang, "GPT-NER: Named Entity Recognition via Large Language Models," arXiv:2304.10428, 2023.

[6] B. T. Willard and R. Louf, "Efficient Guided Generation for Large Language Models," arXiv:2307.09702, 2023.

[7] Y. Ge, S. Das, Y. Guo, and A. Sarker, "Improving Few-shot Named Entity Recognition for Large Language Models Using Structured Dynamic Prompting with Retrieval-Augmented Generation," *npj Artificial Intelligence*, 2025.

[8] E. Fithian and K. Skobelev, "DELM: A Python Toolkit for Data Extraction with Language Models," arXiv:2509.20617, 2025.

[9] T. Calò and L. De Russis, "Leveraging Large Language Models for End-User Website Generation," in *Proc. IS-EUD*, Springer LNCS 13917, 2023.

[10] C. Si, Y. Zhang, Z. Yang, R. Liu, and D. Yang, "Design2Code: Benchmarking Multimodal Code Generation for Automated Front-End Engineering," in *Proc. NAACL*, 2025.

[11] I. Gur, O. Nachum, Y. Miao, M. Safdari, A. Huang, A. Chowdhery, S. Narang, N. Fiedel, and A. Faust, "Understanding HTML with Large Language Models," in *Findings of EMNLP*, 2023.

[12] H. Laurençon, L. Tronchon, and V. Sanh, "Unlocking the Conversion of Web Screenshots into HTML Code with the WebSight Dataset," arXiv:2403.09029, 2024.

[13] C. Huang, A. Ma, S. Vyasamudri, E. Puype, S. Kamal, J. B. Garcia, S. Cheema, and M. Lutz, "ACCESS: Prompt Engineering for Automated Web Accessibility Violation Corrections," arXiv:2401.16450, 2024.

[14] W. Wang, Y. Wang, S. Joty, and S. C. H. Hoi, "RAP-Gen: Retrieval-Augmented Patch Generation with CodeT5 for Automatic Program Repair," in *Proc. ESEC/FSE*, 2023.

[15] J.-M. López-Gil and J. Pereira, "Turning Manual Web Accessibility Success Criteria into Automatic: An LLM-Based Approach," *Universal Access in the Information Society*, vol. 24, pp. 837–852, 2024/2025.

[16] Q. Zhang, C. Fang, Y. Xie, Y. Ma, W. Sun, Y. Yang, and Z. Chen, "A Systematic Literature Review on Large Language Models for Automated Program Repair," arXiv:2405.01466, 2024.

[17] G. M. van de Ven, T. Tuytelaars, and A. S. Tolias, "Continual Learning and Catastrophic Forgetting," arXiv:2403.05175, 2024.

[18] A. Othman, A. Dhouib, and A. N. Al Jabor, "Fostering Websites Accessibility: A Case Study on the Use of the Large Language Models ChatGPT for Automatic Remediation," in *Proc. PETRA '23*, ACM, 2023, pp. 707–713.

[19] T. Javed, J. A. Nawale, E. I. George, S. Joshi, K. S. Bhogale, D. Mehendale, I. V. Sethi, et al., "IndicVoices: Towards Building an Inclusive Multilingual Speech Dataset for Indian Languages," in *Findings of ACL*, 2024. arXiv:2403.01926.

[20] W3C, "Web Content Accessibility Guidelines (WCAG) 2.2," W3C Recommendation, October 2023.

---

## Acknowledgement

We express our sincere gratitude to our project guide, **Dr. Sunil Chavan**, for continuous guidance, technical direction and encouragement throughout this work. We thank the Head of the Department and the faculty of the Department of Artificial Intelligence and Data Science, Smt. Indira Gandhi College of Engineering, Ghansoli, for providing the facilities and academic environment that made this project possible. We also thank our families and peers for their support and feedback during the development and review of this project.

| Name | Signature |
|---|---|
| Siddhesh Gangurde | |
| Dhiren Achrekar | |
| Sarvesh Dhanrale | |
| Aayush Tanwar | |

---

## Appendix A — Repository Structure (optional)

```
services/
  asr-service/        # Speech input (8001)
  nlp-service/        # Prompt → StorefrontSpec (8002)
  layout-service/     # Spec → HTML (8003)
  qa-service/         # Multi-viewport accessibility QA (8004)
  publish-service/    # S3 + CloudFront publication
packages/
  schemas/            # Shared Pydantic / JSON Schema / TypeScript types
  common_utils/       # Error hierarchy and shared helpers
data/
  constraint-rules/   # 18 JSON QA constraint definitions
  component-library/  # 84 curated section variants
  seed/               # QA fixtures
voicefront/           # Flutter client
infra/
  docker/             # Compose stack
  terraform/          # S3 bucket and policy
tests/e2e/            # End-to-end pipeline test
```

## Appendix B — Constraint Inventory (optional but strong)

**Table B.1 — Implemented QA constraints (18)**

| Rule ID | Engine | Severity | Reference |
|---|---|---|---|
| `wcag-2.2-aa-alt-text-001` | axe-core | | WCAG 1.1.1 |
| `wcag-2.2-aa-aria-landmark-001` | axe-core | | WCAG 1.3.1 |
| `wcag-2.2-aa-color-only-001` | axe-core | | WCAG 1.4.1 |
| `wcag-2.2-aa-contrast-001` | axe-core | | WCAG 1.4.3 |
| `wcag-2.2-aa-form-label-001` | axe-core | | WCAG 3.3.2 |
| `wcag-2.2-aa-heading-order-001` | axe-core | | WCAG 1.3.1 |
| `wcag-2.2-aa-lang-attr-001` | axe-core | | WCAG 3.1.1 |
| `wcag-2.2-aa-link-text-001` | axe-core | | WCAG 2.4.4 |
| `wcag-2.2-aa-page-title-001` | axe-core | | WCAG 2.4.2 |
| `wcag-2.2-aa-target-size-001` | axe-core | | WCAG 2.5.8 |
| `structural-broken-image-001` | custom | | — |
| `structural-console-error-001` | custom | | — |
| `structural-duplicate-id-001` | custom | | — |
| `structural-empty-link-001` | custom | — | — |
| `structural-table-headers-001` | custom | | — |
| `structural-viewport-meta-001` | custom | | — |
| `structural-viewport-overflow-001` | custom | | — |
| `wcag-2.2-aa-focus-visible-001` | custom | | WCAG 2.4.7 |

> Fill severity from each JSON file; one row is shown with a misaligned cell on purpose — regenerate this table from `data/constraint-rules/*.json` with a short script rather than typing it.
