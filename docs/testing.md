# VoiceStorefront — Testing Strategy

This file exists to answer the question your panel will actually ask: not "do you have targets"
(Table 5 in the theoretical framework already shows that) but "how do you *measure* whether
you hit them." Each section below maps directly to an evaluation-framework row.

## Test pyramid per service

Every `services/*` folder has a `tests/` directory with the same three tiers:
- **Unit tests** — pure functions in `core/`, mocked I/O (no real Whisper call, no real Playwright render).
- **Integration tests** — real model/engine calls within the service, but downstream services mocked.
- **Contract tests** — request/response bodies validated against `api_contracts.md` definitions, run in CI on every PR that touches a route.

`tests/e2e/` (repo root) runs the full voice-in → live-URL-out chain against a staging deploy, not against mocks — this is the only place all five services run for real together.

## Mapping tests to Evaluation Framework targets (Table 5)

| Target | Metric | How it's actually measured |
|---|---|---|
| WER < 5% in-domain | `services/asr-service/tests/integration/test_wer.py` | Runs the 200-utterance retail benchmark set (`data/seed/asr_benchmark/`) through `whisper_engine.py`, computes WER against gold transcripts using `jiwer`. Run manually before each milestone demo, not on every CI push (too slow/costly to run per-commit). |
| Field extraction F1 > 0.90 | `services/nlp-service/tests/integration/test_schema_f1.py` | 500 gold-annotated transcripts → run through `build_schema()` → compare extracted fields against gold JSON, macro-F1 per entity type. |
| WCAG 2.2 AA pass rate > 99% | `tests/e2e/test_wcag_compliance.py` | `axe-core` run against Playwright-rendered pages for every template × viewport combination, plus manual audit sampling per the framework's stated method. |
| Core Web Vitals (LCP/CLS/FID) | `tests/e2e/test_lighthouse_ci.py` | Lighthouse CI against every published storefront in the staging pilot, thresholds as hard CI gates — a regression here fails the build. |
| Post-publish error rate < 0.5% | Not a pre-launch test — a pilot-window metric | Instrumented via error logging on published storefronts (client-side JS error beacon), aggregated over the 30-day pilot. Document this distinction clearly: it's a production metric, not something you can demo in the viva. |
| Avg. repair latency < 800ms | `services/qa-service/tests/integration/test_repair_latency.py` | Timed runs of `repair_engine.py` across a fixture set of known violation types, both FAISS-match and LLM-generated paths measured separately (they'll differ a lot — report both, not just the average, or a panel member who does ML will ask why they're conflated). |
| Time-to-live (TTL) < 5 min | `tests/e2e/test_ttl_stopwatch.py` | Wall-clock timer wrapping the full chain in the e2e suite, run against realistic (not trivial) sample audio. |
| NPS > 65, task completion > 90% | Not a code test | Usability study protocol — needs a separate `pilot_study_protocol.md` if you want this documented as rigorously as the automated metrics; flag this to your mentors as a distinct methodology, not an engineering deliverable. |

## What's explicitly NOT tested in MVP (say this proactively, don't wait to be asked)
- No load/stress testing — single-tenant MVP, concurrency isn't a claimed property.
- No fuzz testing on the ASR upload endpoint beyond format/size validation — full security fuzzing is out of scope (see `security.md`).
- No automated regression suite for the FAISS repair-rule quality over time (i.e. verifying repairs don't degrade as the index grows) — this is a real gap given the framework's continual-learning claims, and it's worth naming as future work rather than pretending it's covered.

## CI gating policy
- Unit + contract tests: block every PR merge.
- Integration tests: run on merge to `main`, not on every push (model calls are slow).
- E2E suite: run nightly + manually before any mentor demo, not on every merge.
