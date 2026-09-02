# Person A — Voice-to-Text (asr-service)

Owns: `services/asr-service/` — everything between raw audio in and a clean transcript out.
Read `Architect.md` (L2 section) and `data.md` if you need the "why" behind any step below.

---

## Phase 0 — Setup

- [ ] Clone the repo once it exists; run `scaffold_project.ps1` if you're the one setting it up, otherwise just pull after someone else runs it.
- [ ] Install Docker; confirm `docker compose -f infra/docker/docker-compose.dev.yml up --build` runs on your machine.
- [ ] Copy `services/asr-service/.env.example` to `.env`, fill in local values per `environment.md`.
- [ ] Get a free Groq API key, set `GROQ_API_KEY` in your `.env`.
- [ ] Confirm you can hit your own stub service's root endpoint once it's in the compose file.
- [ ] Sign off in writing (team doc) that you own `asr-service` — Tracks aren't assumed, they're recorded.

## Phase 1 — Foundation

**Shared, do this with the team before touching your own code:**
- [ ] Sit in on the `StorefrontSpec v1.0` schema review (`packages/schemas/storefront_spec.schema.json`) — even though you don't build it, your output (`language`, `transcript`) feeds directly into it, so flag now if something doesn't fit what ASR can realistically output.

**Your own work — you no longer install or run Whisper locally; it runs on Groq's API (see `inference_hosting_plan.md`):**
- [ ] Confirm your Groq key works against the Whisper endpoint on a sample Hindi and English clip.
- [ ] Test a Marathi clip specifically and write down what happens — don't assume it works, Groq's Marathi support isn't well documented (see `Architect.md` L2). This matters for scoping, not just curiosity — the framework already lists Marathi as a stretch goal, so a weak result here isn't a crisis.
- [ ] Download and prep the Mozilla Common Voice (Hindi, Marathi, Tamil) subset into `data/seed/` — for benchmarking Groq's accuracy, not for training anything yourself.
- [ ] Write `services/asr-service/core/language_detect.py` — IndicLID wrapper, runs on the first 5s of audio.
- [ ] Write `services/asr-service/core/whisper_engine.py` — calls Groq's `whisper-large-v3` endpoint (via the shared `packages/common-utils/groq_client.py`), passing the detected language as the `language` parameter.
- [ ] Write `services/asr-service/core/validation.py` — magic-byte check, format check (`ASR_ALLOWED_FORMATS`), duration check (`ASR_MAX_AUDIO_DURATION_SEC`). This runs **before** anything reaches Groq — a bad file now wastes a real API call against your team's shared quota, not just local CPU time.
- [ ] Write `services/asr-service/routers/transcribe.py` wiring: validation → language_detect → whisper_engine, matching the request/response shape in `api_contracts.md` (`POST /v1/asr/transcribe`).
- [ ] Write unit tests in `services/asr-service/tests/unit/` with **mocked** Groq responses — never call the real API in unit tests, save the quota for integration/e2e runs.

## End of Phase 1 checkpoint
- [ ] Your service returns a real `{transcript, language, confidence, segments}` response for at least one real recorded clip, matching the shape in `api_contracts.md`.
- [ ] Confirm with Person B that the response shape you're producing is exactly what `nlp-service` expects as input.

## Later, worth knowing now
Month 5 includes a one-time rented-GPU validation run (`deployment.md` §7) to confirm genuinely
self-hosted Whisper still works, backing up the framework's "self-hostable" claim. You'll likely
be the one running that specific comparison — it's a few hours, not a new ongoing responsibility.
