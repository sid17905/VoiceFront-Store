# AGENT CONTRACT — Executable Task Graph

**For:** an autonomous coding agent working in `F:\VoiceFront-Store`.
**Read first:** `docs/INVARIANTS.md` (what not to change), `docs/DECISIONS.md` (what not to decide).
**Execution rule:** run steps **in graph order**. Do not start a step whose dependencies are not green.
**Definition of done:** `python scripts/verify_step.py <STEP_ID>` exits **0**, and you paste its output into the PR.

---

## 0. How to work

```
1. Read docs/INVARIANTS.md and docs/DECISIONS.md (once per session).
2. Run: python scripts/verify_step.py --list
3. Pick the next step whose deps are GREEN and whose status is PENDING.
4. Read the step's allowed_files. Do not touch anything else.
5. Make the change.
6. Run its proof. If it fails: fix once. If it fails again for the same reason: STOP and report.
7. Update docs/state.json: {"<STEP>": {"status": "green", "proof": "<output tail>", "at": "<ISO>"}}
8. Commit: "fix(<area>): <step id> <one-line>" with the proof in the body.
```

**Never:** push, apply Terraform, rotate keys, edit `.env`, delete fixtures, weaken tests, rewrite docs outside D-steps.

---

## 1. Task graph

Status: `PENDING` · `GREEN` · `BLOCKED`. Dependencies must be `GREEN` before a step starts.

### Phase G — Guardrails

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **G0** | Record the baseline | — | `tests/baseline.json` | `python scripts/verify_step.py G0` |
| **G1** | Rotate the four Groq keys *(HUMAN)* | — | none | manual: new key works via `/health` |
| **G2** | Create `audit-fixes` branch, commit current tree | G0 | `.gitignore`, `.gitattributes` | `git status --short` empty |
| **G3** | Back up the working tree *(HUMAN)* | — | none | a copy exists outside the repo |

### Phase S — Security (PR-1, PR-2)

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **S1** | `autoescape=True` in the Jinja env | G2 | `services/layout-service/core/renderer.py`, `tests/layout/test_xss.py` | XSS test fails before, passes after |
| **S2** | JSON-LD built in Python; `{{ json_ld \| safe }}` in all 5 templates | S1 | `renderer.py`, `templates/*.jinja2`, `tests/layout/test_jsonld.py` | every category's JSON-LD parses |
| **S3** | `safe_version_id` / `safe_child`; use in QA + publish | G2 | `packages/common_utils/validators.py`, `qa/routers/qa.py`, `publish/routers/publish.py`, `publish/core/s3_uploader.py`, tests | traversal cases raise |
| **S4** | SSRF guard on `/scrape`; `asyncio.to_thread`; size caps | G2 | `layout/routers/scrape.py`, `tests/layout/test_scrape_guard.py` | private/loopback/file/gopher rejected |
| **S5** | Remove the fingerprint script | S1 | `renderer.py` | no `__voicefront_fingerprint` in output |
| **S6** | No default WhatsApp; no dead asset paths; placeholder SVG | S1 | `renderer.py`, templates | spec without contact emits no `wa.me` |
| **S7** | `_PAGE_SHELL` → `templates/_fallback.jinja2`; log original error | S1 | `renderer.py`, `templates/_fallback.jinja2` | forced missing template returns full HTML |
| **S8** | `price_display` / `location_display` helpers | S1 | `renderer.py`, templates | `price=None` renders "Ask for price" |
| **S9** | Empty `LAYOUT_TEMPLATE_DIR` falls back | G2 | `renderer.py` | `""` and `"   "` both render |
| **S10** | Secrets/config hygiene | G1 | `.env.example`, `packages/common_utils/auth.py`, all `main.py`, `.gitignore` | `grep` for secrets empty |
| **S11** | Auth + rate limits + body caps | S3 | all `main.py`, `requirements.txt`, `packages/common_utils/security.py` | 429 and 401/403 tests |
| **S12** | `.dockerignore`, non-root, python healthchecks | G2 | `.dockerignore`, `services/*/Dockerfile`, `docker-compose.dev.yml` | compose config validates |

### Phase A — Architecture repairs

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **A1** | Single `groq_client.py`; all three call sites use it | S10 | `packages/common_utils/groq_client.py`, `whisper_engine.py`, `schema_builder.py`, `repair_engine.py` | one `grep` finds no direct Groq URL/SDK use |
| **A2** | `service_app.py` factory (CORS, request-ID, errors, logging filter) | S10 | `packages/common_utils/service_app.py`, all `main.py` | all five expose `/health` with the same shape |
| **A3** | Generate JSON Schema + TS from Pydantic; CI drift check | A1 | `packages/schemas/*`, `scripts/gen_schemas.py` | regenerating produces no diff |
| **A4** | Editable installs; delete `sys.path.insert` blocks | A2 | `packages/pyproject.toml`, service `pyproject.toml`, imports | tests import without path hacks |

### Phase L — Layout

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **L1** | Per-category templates render; fallback only on template errors | S7 | `renderer.py` | 5 categories, distinct templates |
| **L2** | `render_components` really assembles variants | S1 | `renderer.py`, `routers/generate.py` | unique variant marker appears |
| **L3** | Dedupe + `PENDING` default for harvested variants | L2 | `tools/dedupe_components.py`, `data/component-library/**` | unique-body count reported |
| **L4** | Page correctness: lang, meta, OG, landmark, alt, tap targets | S8 | templates, `renderer.py` | per-category snapshot assertions |
| **L5** | Layout Dockerfile installs Chromium or drops scraping deps | S12 | `layout/Dockerfile`, `requirements.txt` | image builds |

### Phase Q — QA

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **Q1** | Add `httpx` to QA requirements | G2 | `qa/requirements.txt` | import succeeds |
| **Q2** | Correct status codes (400/404/500) | S3 | `qa/main.py`, `qa/routers/qa.py`, `common_utils/exceptions.py` | code-mapping test |
| **Q3** | Node-anchored deterministic repair; LLM constrained | Q1 | `qa/core/repair_engine.py`, `tests/qa/test_repair.py` | fixture 6 violations → 0 critical |
| **Q4** | Return `repaired_html`; persist repairs; per-violation flags | Q3 | `qa/routers/qa.py` | response contains repaired HTML and re-detected flags |
| **Q5** | `passed` = no critical; document `pass_rule` | Q4 | `qa/routers/qa.py`, `docs/procedure/api_contracts.md` | test with only minor issues passes |
| **Q6** | Focus probe fix | Q3 | `qa/core/detect_engine.py` | probe test |
| **Q7** | SORT ranks by stored failure frequency | D-09 | `qa/core/sort_engine.py`, `qa/core/history.py` | ranking changes after history |
| **Q8** | LEARN stores confirmed patches; reuse | Q7 | `qa/core/learn_engine.py`, `qa/core/history.py` | second run uses stored patch |

### Phase N/A — NLP and ASR

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **N1** | Honor `GROQ_MODEL` | A1 | `schema_builder.py` | call uses env model |
| **N2** | No `food` default; `category` invalid → `is_valid=false` | N1 | `schema_builder.py` | no-price prompt stays invalid |
| **N3** | Tagline word-index fix | N1 | `schema_builder.py` | named-shop tagline sane |
| **N4** | `max_length`; `invalid_fields` shape | N2 | `routers/extract.py`, `entity_types.py` | 422 over 4000 chars; shape matches docs |
| **N5** | Schema F1 on 30 gold prompts | N4 | `data/seed/storefront_specs/gold/*`, `test_schema_f1.py` | F1 printed and asserted |
| **A1S** | ASR live/simulator separation; 503 on failure | A1 | `whisper_engine.py`, `routers/transcribe.py` | no key → 503, not canned 200 |
| **A2S** | Size + magic-byte validation | A1S | `core/validation.py`, `routers/transcribe.py` | 413 and 400 tests |
| **A3S** | Retry only retryable errors; timeout; shared client | A1S | `whisper_engine.py` | 401 not retried |
| **A4S** | `asyncio.to_thread` | A1S | `whisper_engine.py` | no blocking call |
| **A5S** | WER on ≥20 clips | A2S | `data/seed/asr_benchmark/**`, `test_wer.py` | WER printed and asserted |
| **A6S** | Use Whisper's detected language | A1S | `whisper_engine.py` | response language comes from API |

### Phase P — Publish, and I — Infra

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **P1** | Real server-side QA gate | Q4, A1 | `publish/routers/publish.py` | bad bundle → 409 |
| **P2** | URL matches uploaded key (D-02) | P1 | `publish/core/s3_uploader.py`, `routers/publish.py` | URL contains key path |
| **P3** | Delete or implement `verify_prefix_isolation` | P1 | `s3_uploader.py` | no function returns True vacuously |
| **P4** | Error mapping + CORS | P1 | `publish/main.py`, `routers/publish.py` | 404/409/502 mapping |
| **P5** | Dockerfile + compose entry on 8005 | S12 | `publish/Dockerfile`, `docker-compose.dev.yml` | `docker compose config` shows 8005 |
| **I1** | Compose: remove `deploy`, add `env_file`, `depends_on` | S12 | `docker-compose.dev.yml` | config validates |
| **I2** | CloudFront + OAC; private bucket | D-05 | `infra/terraform/s3_cloudfront.tf` | `terraform validate` |
| **I3** | Backend block, tags, remove empty `.tf` | I2 | `infra/terraform/*.tf` | validate |
| **I4** | CI workflow | S12, T7 | `.github/workflows/ci.yml` | workflow runs on a test PR |

### Phase F — Flutter

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **F1** | Commit lib; fix widget test; lockfile; analyze clean | G2 | `voicefront/lib/**`, `test/widget_test.dart`, `pubspec.*` | `flutter analyze --fatal-infos` |
| **F2** | INTERNET + cleartext config + `--dart-define` base URL | F1 | manifests, `voicefront_backend_service.dart` | release build reaches `/health` |
| **F3** | Real QA call; delete fabricated metrics | F2, Q4 | `voicefront_backend_service.dart`, `chat_screen.dart`, preview | QA counts from backend |
| **F4** | Edits re-render + re-QA | F3 | `chat_screen.dart` | changing hours changes HTML |
| **F5** | Real publish | F3, P1 | client + 3 call sites | publish returns a URL |
| **F6** | `mounted` guards; retry last message; timeouts; cancel | F3 | `chat_screen.dart`, service | no setState-after-dispose |
| **F7** | Escape or delete client fallback HTML | F2 | `voicefront_backend_service.dart` | escaped output |
| **F8** | Execute D-01 | F1 | `voicefront/lib/**`, `main.dart` | no unreachable screens |
| **F9** | Dark mode | F8 | `main.dart`, theme, screens | system brightness respected |
| **F10** | Semantics, text scale, reduced motion, links | F9 | screens, widgets | a11y checklist |
| **F11** | Real mic (optional) | F2, A1S | `pubspec.yaml`, record screen | transcript from ASR |
| **F12** | Execute D-14 | F1 | `apps/web/**` | no 0-byte files |

### Phase T — Tests, and D — Docs

| ID | Task | Deps | Allowed files | Proof |
|---|---|---|---|---|
| **T1** | WCAG compliance script | Q4 | `tests/e2e/test_wcag_compliance.py` | runs, prints pass rate |
| **T2** | TTL stopwatch | Q4, P5 | `tests/e2e/test_ttl_stopwatch.py` | prints end-to-end seconds |
| **T3** | Lighthouse CI | T1 | `tests/e2e/test_lighthouse_ci.py` | produces scores |
| **T4** | Repair latency | Q3 | `qa/tests/integration/test_repair_latency.py` | median printed |
| **T5** | Contract tests | S11 | `tests/contract/**` | 400/404/409/422 covered |
| **T6** | Golden prompt set + results table | N5, L4 | `tests/eval/**`, `docs/results.md` | table regenerated |
| **T7** | `testpaths`; coverage gates | T1–T6 | `pytest.ini`, `requirements-dev.txt` | root pytest collects only project tests |
| **T8** | Coverage threshold | T7 | `pytest.ini` | CI fails below 80 % |
| **D1** | README | all | `README.md` | quickstart works |
| **D2** | `CLAUDE.md` | D1 | `CLAUDE.md` | present |
| **D3** | `.gitattributes` + renormalise | G2 | `.gitattributes` | diff has no CRLF-only files |
| **D4** | Fix `UPDATES.md` | D1 | `docs/UPDATES.md` | no unsupported claim |
| **D5** | Update plan/implementation docs | D4 | `docs/v2/*`, `docs/*_COMPLETE.md` | matches code |
| **D6** | Deck per `DECK_CHANGES_v2.md` | D5 | deck binaries (human) | human review |
| **D7** | Chapter 4 tables | T6, T2, T4 | `docs/PROJECT_REPORT_BE.md` | measured numbers |

---

## 2. Reporting format (every step)

```md
### STEP <ID> — <title>
- **Changed:** <file:line list>
- **Why:** <invariant / audit finding>
- **Proof:** `<command>` → exit 0
- **Output (tail):**
  ```
  <last 10 lines>
  ```
- **Risks:** <what could still be wrong>
- **Next:** <step id>
```

If any field cannot be filled honestly, the step is not done.

---

## 3. Anti-hallucination rules specific to this repo

1. **Run from the service directory or set `PYTHONPATH`.** `core` is a namespace shared by five services; importing from the wrong cwd loads the wrong `core`.
2. **`pytest` without `testpaths`** will walk `scrapy/` and `.venv/`. Always pass an explicit path until T7 lands.
3. **The QA service needs Chromium and axe-core.** If `playwright` or `node_modules/axe-core` is missing, the proof is `SKIP (missing browser)`, never `PASS`.
4. **The ASR/NLP live paths need `GROQ_API_KEY`.** Without it they use fallbacks; a "green" test may be testing the fallback. State which mode ran.
5. **The Flutter app's backend is `10.0.2.2`** — an emulator alias. A host-side curl is not a client test.
6. **Do not infer a rule count.** It is 18 (`data/constraint-rules/*.json`). Recount before writing a number.
7. **Do not infer component counts.** 84 files, 28 unique bodies (as of 2026-10-18). Recount after any change.
