# VoiceStorefront — Procedure Plan by Person (4-Way Split)

Same plan as `procedure_plan.md`, reorganized so each person can look at one column and know
exactly what they're doing, phase by phase. Track ownership from `milestones.md`:

- **Person A** — Voice-to-text (asr-service)
- **Person B** — Understanding / schema-building (nlp-service)
- **Person C** — Page-building (layout-service)
- **Person D** — Quality-checking + publishing (qa-service + publish-service)

Rename the columns to actual names once you've assigned them — the work doesn't change, only the label does.

---

## Phase 0 — Setup (everyone, together)
| Everyone |
|---|
| Create repo, run the scaffold script, get Docker running on all 4 machines, confirm the assignment above in writing. Get a free Groq API key each and confirm one test call works. Buy the project domain (~$10/year). |

---

## Phase 1 — Lock the Foundation

| Person A (voice-to-text) | Person B (understanding) | Person C (page-building) | Person D (quality-check) |
|---|---|---|---|
| Confirm Groq's hosted speech-to-text works on a sample clip (Hindi, English, and test Marathi specifically) | Confirm Groq's hosted LLM responds correctly to a test prompt | Hand-build the first template (food category) | Draft the first 15–20 quality-check rules |
| Write language-detection wrapper | Draft few-shot examples for schema-filling | Build the colour-palette logic for that one category | Set up Playwright, confirm it can render a page at 5 screen sizes |
| Write the core transcription logic (calls Groq, not a local model) | Write the "fill in the schema" logic (calls Groq) | Build the page-rendering logic | Write a basic version of the violation-scanner (no auto-fix yet) |
| Write upload safety checks (file type/size) — matters more now, since a bad upload wastes a real API call against your shared quota | Write the "check the schema is valid, retry if not" logic | Stub the "which template to use" logic (always pick food for now) | Set up file storage (S3) and confirm upload works |

**Together first, before any of the above:** agree on and freeze the exact shape of the data every piece will pass around (the "shop info" format). Nothing above can really start until this is locked. Nobody installs Whisper or an LLM locally — everyone points at Groq instead, which is why laptop specs stopped being a blocker.

---

## Phase 2 — One Thing Working End to End

| Person A | Person B | Person C | Person D |
|---|---|---|---|
| Support the first real recordings being tested | Connect: transcript → structured shop info | Connect: structured shop info → rendered page | Run the scanner against the first *real* rendered pages (not fake ones) |
| Start collecting real shop-owner recordings for later accuracy tuning | Fix whatever the first real recordings reveal about missing/wrong fields | Fix layout bugs the first real data reveals | Note down what kinds of problems show up most, to prioritize Phase 3 rules |

**Together:** build the recording screen and the review/edit screen in the app, and wire them to each other. Test with 2–3 recordings of a fake shop description. **Checkpoint: live demo of voice-in → rendered page.**

---

## Phase 3 — Add Quality Checking

| Person A | Person B | Person C | Person D |
|---|---|---|---|
| Benchmark Groq's accuracy on real shop-owner recordings (can't fine-tune Groq's hosted model directly — this is measurement, not training) | Stress-test schema-building against messy/ambiguous speech | Build the remaining 4 category templates | Build the real "which violations matter most" ranking logic |
| Run the first real accuracy benchmark, write down the number | Run the first real "did we extract the right fields" benchmark | Build the real "which template fits this shop" classifier across all 5 categories | Expand the violation-scanner toward the full rule set |

**Checkpoint:** full pipeline runs across all 5 categories and produces a real quality report (even if it still finds problems it can't fix yet).

---

## Phase 4 — Self-Healing + Go Live

| Person A | Person B | Person C | Person D |
|---|---|---|---|
| Support end-to-end timing tests (helps debug where time is spent) | Support end-to-end tests, fix schema edge cases surfaced | Support end-to-end tests, fix layout edge cases surfaced | Build the auto-fix logic: match known fixes first, fall back to AI-generated fixes for new problems |
| — | — | — | Build "publish" — page goes live with a real URL, only after quality checks pass |

**Together:** run the whole pipeline start to finish, time it against your 5-minute target. **Checkpoint:** at least one category goes voice-in to live page with no serious problems left.

---

## Phase 5 — Real Users

| Person A | Person B | Person C | Person D |
|---|---|---|---|
| Re-run the accuracy benchmark against Groq, record the real number; help run the one-time rented-GPU comparison (self-hosted vs. Groq) | Re-run the field-extraction benchmark, record the real number | Support any layout bugs found by real users | Run the full quality-check benchmark across all templates and screen sizes |
| — | — | — | Do the security pass: upload safety, rate limits (now protecting your shared Groq quota too), storage permissions |

**Together:** recruit your pilot users, launch the trial period, and start collecting feedback as early as possible — this is the one part of the whole plan with no slack, since it needs real calendar time, not just effort.

---

## Phase 6 — Wrap Up

| Everyone, together |
|---|
| Fix what real users found broken |
| Compile your actual results against your original targets — the honest gaps included |
| Freeze the code, no more feature changes |
| Write the final report |
| Rehearse the live demo — more than once, on the actual equipment you'll present with |
| Prepare answers for the hard questions your panel will ask |
| Submit |

---

## The one rule that keeps this from falling apart
Person D (quality-checking) can't do real work until Person C (page-building) is producing real pages, and Person C can't do real work until Person B (understanding) is producing real structured data. If any one person falls behind, everyone downstream stalls — check in with each other at the end of every phase, not just at the big checkpoints.
