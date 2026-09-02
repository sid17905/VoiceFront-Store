# Person D — Quality-Checking + Publishing (qa-service + publish-service)

Owns: `services/qa-service/` and `services/publish-service/` — everything between a rendered
bundle in and either a repaired/validated report or a live URL out. Read `Architect.md` (L5
section) and `data.md` for the "why." Heads up from the work-hour breakdown: this role carries
the heaviest total load over the project (Phase 4 especially) — Phase 0/1 being lighter is
intentional, not a sign you're behind.

---

## Phase 0 — Setup

- [ ] Pull the repo once scaffolded; confirm Docker Compose runs on your machine.
- [ ] Copy both `services/qa-service/.env.example` and `services/publish-service/.env.example` to `.env` per `environment.md` (`QA_FAISS_INDEX_PATH`, `QA_SIMILARITY_THRESHOLD`, `QA_VIEWPORT_WIDTHS`, `PUBLISH_S3_BUCKET`, `PUBLISH_CLOUDFRONT_DIST_ID`).
- [ ] Set up a dev AWS account/S3 bucket if the team doesn't have one yet — you'll need it sooner than the others.
- [ ] Get a free Groq API key, set `GROQ_API_KEY` in your `.env` — you'll need this in Phase 4 when `repair_engine.py`'s LLM-assisted fallback goes in, but grab the key now while everyone else is doing the same.
- [ ] Confirm you can hit both stub services' root endpoints once they're in the compose file.
- [ ] Sign off in writing that you own both `qa-service` and `publish-service`.

## Phase 1 — Foundation

**Shared, do this with the team first:**
- [ ] Sit in on the `StorefrontSpec v1.0` schema review — mainly to sanity-check that whatever fields exist will actually be checkable (e.g. if `contact.whatsapp` is optional, decide now whether a missing contact is a QA violation or not).

**Your own work — note this phase is deliberately about groundwork, not the full pipeline:**
- [ ] Draft the first 15–20 constraint rules in `data/constraint-rules/*.json` (contrast ratio, alt-text presence, viewport overflow) using the format in `data.md`.
- [ ] Set up Playwright headless Chromium locally; confirm it renders a static HTML file at all 5 target viewport widths (320/375/768/1024/1440).
- [ ] Write a minimal `services/qa-service/core/detect_engine.py` that runs your 15–20 rules against a rendered page and returns a violation list — no auto-repair yet.
- [ ] Stub `core/sort_engine.py`, `core/repair_engine.py`, `core/learn_engine.py` as simple pass-throughs — the real logic isn't due until Phase 3–4, and building it now would mean testing against fake data since Person C won't have real rendered pages yet. When `repair_engine.py` becomes real, its LLM fallback calls Groq via `packages/common-utils/groq_client.py` — not a locally-hosted model, which is genuinely good news given your hardware (see `hardware.md`).
- [ ] Write `services/publish-service/core/s3_uploader.py` against your dev bucket — confirm a file uploads and is publicly readable **only** at the intended prefix (test this negatively too — confirm other prefixes stay private).

## End of Phase 1 checkpoint
- [ ] Your `detect_engine.py` can scan a static sample HTML fixture and return real violations.
- [ ] Your S3 upload path works end to end on a test file.
- [ ] Confirm with Person C when their first real rendered page is ready — that's the moment your Phase 2 work actually starts being useful, so don't let this checkpoint slip without telling them.

## Why this matters more for you than anyone else on the team
The whole point of routing Whisper and Llama-3 through Groq instead of self-hosting (per
`inference_hosting_plan.md`) is that your machine's 2 GB VRAM stops being a constraint anywhere
in this pipeline — including the repair-engine's LLM fallback, which is the single most
GPU-dependent piece your role owns. You don't need to work around your hardware here; the plan
already did that for you.
