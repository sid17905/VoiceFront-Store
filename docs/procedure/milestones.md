# VoiceStorefront — Milestones & Timeline

Maps the theoretical framework's 5-layer architecture + QA pipeline onto a 6-month academic
calendar for a 4-person team. Built around parallel tracks — with 4 people and 5 services, full
serial execution (L1 → L2 → L3 → L4 → L5) wastes 3 of the 4 people at any given time.

## Suggested track ownership (adjust to actual skills/interest, but assign explicitly — don't
let ownership stay ambiguous)
- **Track A:** asr-service (L1 + L2)
- **Track B:** nlp-service (L3)
- **Track C:** layout-service (L4)
- **Track D:** qa-service + publish-service (L5) — this track has the most dependencies on the
  others being functional first, so whoever owns it should spend early months on `data/constraint-rules/`
  and the FAISS/Playwright scaffolding rather than sitting idle.

`apps/web` is a shared responsibility, built incrementally alongside whichever service it's
currently wiring to — not a 5th person's job, since there are only 4 of you.

## Month-by-month

**Month 1 — Foundations, not features**
- Finalize and freeze `StorefrontSpec v1.0` in `packages/schemas` — every track depends on this,
  so it's the one thing that must be locked before parallel work starts.
- Repo scaffold per `files.md`, Docker Compose dev environment working end-to-end (even with
  stub/mock services), CI skeleton.
- **Get everyone a Groq API key and confirm a basic call works (Whisper transcription + a Llama-3 chat completion) — this replaces "set up local Whisper/Ollama" entirely, per `inference_hosting_plan.md`. Do this in week 1, not whenever someone gets to it, since Tracks A and B both depend on it immediately.**
- **Buy the project domain (~$10/year) and point DNS at what will become the CloudFront distribution — cheap to do early, annoying to do under deadline pressure later.**
- Track A: confirm Groq's Whisper endpoint handles Hindi and English test clips correctly; test a Marathi clip specifically and note the result (don't assume it works — see `Architect.md` L2).
- Track B: NER model fine-tuning setup (still local — IndicBERT is small), few-shot prompt drafts tested against Groq's Llama-3 endpoint.
- Track C: pick and hand-build the first of the 5 category templates.
- Track D: draft the first 15–20 constraint rules (of the 50 target) in `data/constraint-rules/`.
- **Checkpoint:** everyone can run `docker compose up`, hit their own service's health endpoint, and confirm their Groq API calls succeed.

**Month 2 — Vertical slice, one category only**
- Get one full path working: voice → transcript → spec → rendered page (food category only,
  no QA yet). This is the first point you can actually demo something, even if rough.
- Track A: begin retail-domain field recording — used for evaluating Groq's real-world accuracy on retail speech, not for local fine-tuning (Groq's hosted model isn't something you fine-tune yourselves; if accuracy on retail-domain speech is weak, that's a finding for Month 5's self-hosted comparison, not something to fix by retraining Groq's model).
- Track D: Playwright headless rendering working across the 5 viewport widths, no repair logic yet.
- **Checkpoint (mid-term review candidate):** live demo of voice-in → rendered (unvalidated) HTML.

**Month 3 — QA pipeline comes online**
- Track D: SORT + DETECT phases functional against the constraint rules from Month 1–2.
- Track A: WER benchmark run against the 200-utterance set through Groq (see `testing.md`) — this is your first real evaluation-framework number, not a target anymore. Watch the daily/per-minute rate limit while running this.
- Track B: schema validation retry loop implemented and tested against edge-case transcripts.
- Track C: remaining 4 category templates built.
- **Checkpoint:** QA report generation working (violations detected, not yet auto-repaired).

**Month 4 — Self-healing + publish**
- Track D: REPAIR phase (FAISS matching + Groq-hosted LLM-assisted repair) and LEARN phase implemented.
- publish-service integrated: S3 + CloudFront, live URL returned, served from your actual domain.
- First full end-to-end run, all 5 categories, timed against the <5 min TTL target — this timing now includes real Groq API round-trip latency, which is a more honest number than a local-only test would give you.
- **Checkpoint:** full pipeline demo, voice-in to live published URL, at least one category
  passing QA with zero critical violations.

**Month 5 — Hardening + evaluation**
- Run every metric in `testing.md`'s evaluation-framework mapping table for real: WER, F1,
  WCAG pass rate, Core Web Vitals, repair latency, TTL — all against Groq.
- **Rent a GPU box for a few hours (`deployment.md` §7) and re-run the WER/F1 benchmarks against genuinely self-hosted Whisper/Llama — this is the one point in the whole project where self-hosted infrastructure actually gets used, specifically to back up Table 4's "self-hostable" claim with a real number.**
- Begin the pilot cohort (50 users) for NPS/task-completion/post-publish-error-rate — these need
  the longest lead time (30-day window per the framework), so starting late in Month 5 is already
  tight against a 6-month deadline; flag this explicitly to mentors if the pilot start slips.
- Security pass per `security.md` (upload validation, rate limiting — now protecting your shared Groq quota too, not just server load — bucket policy audit).
- **Checkpoint:** all automated metrics measured at least once (both Groq-hosted and self-hosted), pilot cohort live.

**Month 6 — Report, defense prep, pilot close-out**
- Close out the 30-day pilot window, compile NPS/completion/error-rate results.
- Freeze the codebase; write the final report against the actual measured numbers, not the
  targets — Table 5/Table 6 in the framework are targets, and the report needs to show target
  vs. actual, including where you fell short (a panel trusts a team more when the gaps are
  acknowledged, not hidden).
- Rehearse the live demo end-to-end at least twice under conditions matching the actual defense
  (same network, same hardware) — most student-team demo failures are environment mismatches,
  not code bugs.
- **Checkpoint:** final submission + defense.

## Dependency risks worth tracking explicitly (add to a shared risk log, don't just keep this in someone's head)
- Track D (QA) is blocked on Track C (layout) producing real HTML to validate against — if
  layout-service slips, Track D has nothing to test on. Mitigate by having Track D validate
  against the static seed fixtures in `data/seed/` from Month 1, not waiting for real output.
- The 30-day pilot window is the single least-flexible constraint in this timeline — everything
  upstream of Month 5 has some slack; the pilot does not, because it's calendar time, not effort.
