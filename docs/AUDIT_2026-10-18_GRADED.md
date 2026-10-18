# VoiceFront-Store — Graded Codebase Audit

**Date:** 2026-10-18 · **Commit audited:** `2428a6f` + working tree
**Audited against:** `docs/_planning_audit/07_FIVE_PHASE_SCOPE_AND_PRESENTATION_PLAN.md` (acceptance A1–A5),
`docs/PROJECT_REPORT_BE.md` (FR-1…FR-9, NFR-1…NFR-5, Tables 4.1–4.4),
`docs/procedure/{VoiceFront_Store_PROJECT_ABSTRACT,testing,api_contracts,milestones}.md`,
`docs/v2/MASTER_PLAN_V2_FINAL.md`, `docs/DECK_CHANGES_v2.md`.

> **Reading rule used throughout:** a feature is graded **only** by what the repo can demonstrate
> on demand. A function that exists but is never called, a test file that is empty, and a slide that
> claims it, all score zero. This is the same rule the deck-review document already applies.

---

## 0. Scorecard

| # | Area | Grade | Score | One-line verdict |
|---|---|---|---|---|
| 1 | NLP extraction (Phase 2) | **A−** | 92 | Real LLM path + validation loop + offline fallback; no F1 measurement |
| 2 | Layout rendering (Phase 3) | **C** | 65 | Renders to a demo screen, but templates are half-broken, the fallback shell crashes, assets are missing, JSON-LD is injectable |
| 3 | QA detection + repair (Phase 4) | **B** | 80 | Genuine multi-viewport axe-core DETECT; repair now wired but unsafe; SORT/LEARN are stubs |
| 4 | ASR (Phase 1) | **C** | 62 | Real Groq call exists; simulator fallback is hardcoded; no real audio, no WER, no LID |
| 5 | Publishing (Phase 5) | **C−** | 58 | S3/CloudFront code is solid; QA gate returns `True`; Dockerfile is 0 bytes; no CloudFront resource |
| 6 | Flutter client | **C+** | 70 | Chat → NLP → layout works; QA never called, edits don't re-render, publish is a no-op, ~1,150 lines are unreachable, release build can't reach the backend |
| 7 | Shared schemas & API contracts | **B−** | 76 | Pydantic SSOT is clean; contract drift, TS client field mismatch, no schema version |
| 8 | Testing & evaluation | **D** | 52 | 3 of 4 E2E files are 0 bytes; the 4th fails; the widget test doesn't compile; the "eval" harness asserts nothing |
| 9 | Infrastructure & CI | **C−** | 58 | Compose boots on paper; no CI, 0-byte Dockerfiles, empty `.tf` files, healthchecks lack `curl` |
| 10 | Security | **D+** | 57 | Live Groq keys on disk, no auth, no rate limit, open `/scrape`, stored XSS, path traversal |
| 11 | Docs/claims integrity | **D** | 55 | Three mutating docs contradict the code; fabricated UI metrics; one claimed feature doesn't exist |
| 12 | Visual/UX design | **C+** | 70 | Coherent M3 theme on the chat path; dark mode broken on the legacy screens; no semantics anywhere |
| | **Weighted overall** | **C+** | **≈ 69 %** | Strong semester-1 engineering core; production claims are not yet supportable |

Weights: NLP 15, Layout 15, QA 10, ASR 5, Publish 5, Flutter 15, Schemas 5, Tests 10, Infra 5, Security 5, Docs 5, Visuals 5.

**Letter-scale used:** A ≥ 90 · A− 85–89 · B+ 82–84 · B 78–81 · B− 74–77 · C+ 70–73 · C 65–69 · C− 60–64 · D+ 55–59 · D 50–54.

---

## 1. Acceptance criteria (the document's own yardstick)

| ID | Criterion (from `07_…` §8) | Status | Evidence |
|---|---|---|---|
| **A1** | ≥3 English prompts return `is_valid: true`, correct category, ≥1 priced product | **PASS (by construction)** | Groq path + regex fallback (`schema_builder.py:134-195`). Not measured on a fixed prompt set — no results table exists. |
| **A2** | All 5 categories render name, products+prices, `wa.me`, viewport meta, correct JSON-LD `@type` | **PARTIAL** | `renderer.py:_render_json_ld` maps 5 types correctly, but `render()` loads the `.jinja2` templates whose JSON-LD hardcodes `FoodEstablishment` in `food.jinja2` and omits type parity elsewhere; product images point at a non-existent `assets/` tree |
| **A3** | `/v1/qa/run` on a generated page returns a real violation report from a real browser | **PASS (code-complete)** | `detect_engine.py` uses real Playwright + injected axe-core; unit-tested with a FakePage only — no committed evidence of a real-browser run |
| **A4** | Rehearsed < ~1-minute path that still works offline | **PARTIAL** | Offline works end-to-end via regex fallback; Flutter path is wired to localhost |
| **A5** | `docker compose up` boots asr/nlp/layout/qa healthy | **PLAUSIBLE, UNVERIFIED** | Compose is well-formed; QA image installs axe-core correctly; no CI job has ever run it |

**A-score: 1 pass, 2 partial, 1 pass-with-caveat, 1 unverified.**

---

## 2. Report requirements (FR/NFR in `PROJECT_REPORT_BE.md`)

| ID | Requirement | Status | Note |
|---|---|---|---|
| FR-1 | Prompt **or audio** → spec | ✅ / ⚠️ | Text yes; audio endpoint exists but no client uses it and the simulator ignores the file |
| FR-2 | Validate against shared schema, report invalid fields | ✅ | Pydantic + `invalid_fields`; however `invalid_fields` is `list[str]`, not the documented `[{field, reason}]` |
| FR-3 | Render all 5 categories | ✅ | Fallback shell guarantees a render, but per-category templates are only used if they *don't* raise |
| FR-4 | Page contains name, products+prices, hours, location, WhatsApp, JSON-LD | ⚠️ | Location silently missing: templates read `location.raw_text`, a field that **no longer exists** in `LocationInfo` (`entity_types.py:25-31`) |
| FR-5 | Render at 5 viewports, report violations | ✅ | `DEFAULT_VIEWPORT_WIDTHS = [320,375,768,1024,1440]` |
| FR-6 | Classify violations by severity | ✅ | Rule JSON carries severity; `Violation.to_api_dict()` |
| FR-7 | Propose **and apply** repairs | ⚠️ | Now applied, but by whole-document string replacement — can corrupt the page |
| FR-8 | Publish a **passing** bundle | ❌ | `_server_side_qa_passed_check()` returns `True` unconditionally (`routers/publish.py:49-59`) |
| FR-9 | Client displays page + QA summary | ⚠️ | Page yes (WebView); QA summary tab is a hardcoded mockup (`preview_qa_screen.dart`, "Krishna Sweets") and QA is never called from the app |
| NFR-1 | < 10 min end-to-end | Unmeasured | No timing harness |
| NFR-2 | Usable when LLM is down | ✅ | Regex fallback in NLP, heuristic repair, simulator in ASR |
| NFR-3 | Independently deployable + health | ❌ | publish-service has no Dockerfile and is absent from compose |
| NFR-4 | Single schema source in Python **and TS** | ⚠️ | Pydantic + JSON Schema + TS exist but have already drifted (`ProductItem.price` optional in Python) |
| NFR-5 | Never publish a bundle that failed QA | ❌ | The gate is a stub returning `True` |

---

## 3. Phase-by-phase grading with evidence

### Phase 1 — ASR · **C (62)**

| Check | Result |
|---|---|
| Real transcription | Groq `whisper-large-v3`, `verbose_json`, tenacity retry ×3 (`whisper_engine.py:47-75`) — **good** |
| Offline behaviour | Returns a fixed "Tony's Pizza Kitchen" transcript regardless of the uploaded audio (`whisper_engine.py:14-23`) — acceptable as a demo fallback, misleading as a test fixture |
| Language identification | `detect_language()` returns `default` unconditionally (`language_detect.py:4-9`) |
| Normalisation | 3 regexes (whitespace, currency, phone). No Indic pipeline, as documented (`normalize.py:9-20`) |
| Real mic / audio tests | None. `test_wer.py` posts a 44-byte WAV and asserts response shape |
| Validation | Extension/MIME/size check exists (`core/validation.py`) |

**Why C, not lower:** the hosted path is genuinely implemented and defensive.
**Why not higher:** every measured claim (WER) is absent, and the simulator makes the service look healthier than it is in tests.

### Phase 2 — NLP · **A− (92)**

- Two-attempt loop with validation-error re-prompt (`schema_builder.py:161-192`).
- Graceful degradation at three separate points: no key, missing `groq`/`tenacity`, API exception.
- Placeholder-key guard (`PLACEHOLDER_KEYS`) prevents "pretend live" behaviour.
- `source` is propagated into the spec so the UI can label offline output — a nice touch.
- Deductions: `invalid_fields: list[str]` contradicts `api_contracts.md`'s `[{field, reason}]`; the regex fallback invents prices/products when none are given; no F1 harness; no confidence scores.

### Phase 3 — Layout · **C+ (71)**

The most misleading area relative to the docs. In the **same** working tree:

| Document claim | Code reality |
|---|---|
| "5 category templates" | 5 `.jinja2` files exist, but all five carry `<html lang="hi">` and read `location.raw_text` (a removed field). `render()` falls back to `_PAGE_SHELL` on any exception. |
| "component assembly from the 84-variant library" | `render_components(spec, palette, components)` ignores `components` and calls `render()` (`renderer.py:414-419`). `component_picker` is only used by tests. |
| "category palettes" | ✅ real (`palette_engine.py`, 5 palettes) |
| "dynamic imagery" (`UPDATES.md` #2) | Hardcoded Unsplash hero URLs + image paths under `assets/<category>/*.svg` that **do not exist in the repo** → broken images |
| "template switching by chat command" (`UPDATES.md` #3) | **No such code.** `select_template()` returns `spec["category"]` |
| JSON-LD | Emitted, but built with `json.dumps(data)` into a raw `<script>` string (`renderer.py:315-333`) — a `"description"` containing `</script>` breaks out of the block (stored XSS) |
| Fallback shell | **Broken.** `_PAGE_SHELL` contains unescaped JavaScript braces (`(function() {`, `const fingerprint = {`), so `.format()` at `renderer.py:396` raises `ValueError: unexpected '{' in field name`. Any template failure therefore ends in a 500, not a fallback page — confirmed by running the E2E test (see §5.2) |
| Escaping | **Autoescape is effectively OFF.** `select_autoescape(["html"])` enables escaping only for `.html`/`.htm`/`.xml`; the templates are `.jinja2`, so `shop_name`/`description` render verbatim (per jinja2's documented defaults; not executed in this shell because jinja2 is not installed system-wide). The fallback shell escapes manually — but the shell crashes. |
| JSON-LD validity | The template JSON-LD is **syntactically invalid** whenever both `location` and `contact` are present: the `address` object has no trailing comma and the last `openingHoursSpecification` element has a stray one (`food.jinja2:50-69`). Consumers will drop the structured data. |
| Template dir config | `services/layout-service/.env.example` ships `LAYOUT_TEMPLATE_DIR=` (empty). If copied literally, that becomes `Path("")` → `TemplateNotFound` on every render. |
| Product price | `"%.0f" | format(product.price)` raises `TypeError` when `price` is `None` — explicitly allowed by `ProductItem` (`entity_types.py:17`). Because the fallback shell also crashes, a single priceless product turns `/generate` into a 500. |

### Phase 4 — QA · **B (80)**
- DETECT is the strongest engineering in the project: real Playwright, injected axe-core restricted to reviewed rule IDs, 7 custom JS checks, per-viewport results (`detect_engine.py`).
- 18 rules (11 axe-core + 7 structural) — matches the honest number in `DECK_CHANGES_v2.md`, not the "50" or "400+".
- Repair is **now wired** (`routers/qa.py:115-126`), re-detects and reports counts. This is a real improvement over what the deck-review document describes.
- Deductions:
  - **Repair safety:** each violation is repaired by replacing text in the *whole document*; with N violations, patches overwrite each other and the LLM may return a full page. There is no DOM-anchored patching.
  - **Only the last patch survives:** every `RepairResult` is computed against the original document, but the loop assigns them sequentially (`html = r.repaired_html`), so all but the final repair are discarded (`routers/qa.py:121-126`).
  - **Missing dependency:** `repair_engine.py:3` imports `httpx`, but `services/qa-service/requirements.txt` does not list it — the auto-repair path raises `ImportError` inside the container.
  - **Arbitrary HTML:** the LLM's raw response is used as `repaired_html` with no re-detection or sanitization.
  - `focus_indicator_not_removed` uses `getComputedStyle(el, ':focus')`, which cannot observe pseudo-class styles — the check is effectively inert.
  - SORT is a pass-through; LEARN is a no-op (`sort_engine.py`, `learn_engine.py`).
  - `passed` is true only when *every* health-bot rule passes at *every* viewport; combined with the inert focus check and strict tap-target rule, a clean generated page may never pass.

### Phase 5 — Publish · **C− (58)**

- Correct architecture: upload → invalidate → poll to completion → return URL; fails closed (`s3_uploader.py:129-195`).
- Real problems: QA gate stubbed `True`; `verify_prefix_isolation()` does not actually verify public readability; no CloudFront resource in Terraform despite the filename; no Dockerfile, no compose entry; the domain is a placeholder.

---

## 4. Client (Flutter) · **C+ (70)**

The app is **one screen deep**. `main.dart` mounts only `ChatScreen`; the five-screen voice flow is orphaned code.

| Aspect | Grade | Evidence |
|---|---|---|
| Live integration | ✅ NLP + layout | `voicefront_backend_service.dart:53-118` |
| **Reachability** | ❌ | `HomeScreen`, `RecordScreen`, `ReviewEditScreen`, `PreviewQAScreen`, `StorefrontsScreen` are **constructed nowhere** — only their own class declarations reference them. ~1,150 of ~2,000 screen lines are dead. |
| QA integration | ❌ | `qaViolations: 0` hardcoded (`chat_screen.dart:207`); `PreviewQAScreen` is a static mockup *and* unreachable |
| Chat edit loop | ❌ | Any message containing change/update/add/remove/set clones the spec **unmodified** and re-renders it (`chat_screen.dart:166-171`). `set_theme` and `add_banner` write keys the schema does not have — success ticks for no-ops (`:129-135`) |
| Publish | ❌ | Three no-ops: `chat_screen.dart:291`, `webview_screen.dart:113`, `preview_qa_screen.dart:600` (uncalled) |
| History | ❌ | In-memory `AccountManager` with two demo rows; ids get ragged past 9 entries |
| Theme | ⚠️ | Material 3 on the chat path; but `main.dart:10-15` pins `Brightness.dark` status-bar icons regardless of theme, and legacy screens still use fixed white surfaces (`AppColors.white` as a card colour) — dark mode renders white slabs |
| Accessibility | ❌ | **Zero** `Semantics`/`semanticLabel` anywhere; mic button has no tooltip; no reduced-motion handling; fixed-ratio grid overflows at 2× text scale |
| Config | ❌ | Base URLs hardcoded to `10.0.2.2:800{2,3}`; **release `AndroidManifest.xml` has no `INTERNET` permission** (only `debug/` and `profile/` do), so a release build silently falls back every time; no cleartext-traffic config |
| Build health | ❌ | `test/widget_test.dart` pumps `const MyApp()` — that class **does not exist** (`VoiceFrontApp`); `flutter test` fails to compile. `pubspec.lock` is missing `flutter_markdown` and `google_fonts`, both declared in `pubspec.yaml`. |
| Version control | ❌ | **7 of the 22 lib files are untracked** — including `chat_screen.dart` and `voicefront_backend_service.dart`. A clone of HEAD produces a different, non-chat app. |

The single highest-value client change remains **calling `/v1/qa/run` with the generated HTML**; the second is **committing the working tree**, because the runnable app currently exists only on this machine.

---

## 5. Cross-cutting findings

### 5.1 Security (D+)

| Severity | Finding | Location |
|---|---|---|
| **Critical** | **Four live-looking Groq keys sit in `.env` on disk** (line 1, `GROQ_API_KEYS`). They are untracked and absent from git history, so the repo is clean — but the keys are readable by any local process and should be **rotated now**. | `.env` (contents not reproduced here) |
| **High** | Env-var mismatch: `.env` defines `GROQ_API_KEYS` (plural); both services read `GROQ_API_KEY` (singular) and nothing loads a dotenv file — so the keys are not even being used, which is why the offline fallback runs during tests | `whisper_engine.py:54`, `schema_builder.py:154` |
| **High** | Stored XSS: JSON-LD interpolates unescaped user content into `<script>` | `renderer.py:315-333` |
| **High** | Path traversal: `version_id` concatenated into a filesystem path | `routers/qa.py:79-89`, `publish.py:62-73` |
| **High** | SSRF: `/v1/layout/scrape` fetches any user-supplied URL server-side and returns its HTML; no scheme/private-IP/size limits | `routers/scrape.py` |
| **Medium** | No auth, no rate limiting on any endpoint (matters for the shared Groq quota) | all services |
| **Medium** | Client fallback interpolates `shop_name`/`description` into HTML without escaping, then loads it with `JavaScriptMode.unrestricted` | `voicefront_backend_service.dart:116`, `webview_screen.dart:34` |
| **Low** | `apps/web/.env.local` is **tracked** despite matching `.gitignore`; it is 0 bytes today | git index |
| **Low** | Broad CORS defaults `localhost:3000,8080`; containers run as **root**; no `.dockerignore`, so the 49.8 MB `docs.zip` and `node_modules` enter every build context | all `main.py`, Dockerfiles |
| **Low** | Untracked `packages/common_utils/auth.py:6` hard-codes a JWT fallback secret (`JWT_SECRET_KEY` default) and depends on `python-jose`/`passlib`, which appear in no requirements file | `packages/common_utils/auth.py` |
| **Low** | `scrapy/` is a **full nested clone of upstream Scrapy with its own `.git`** (42 MB). Never `git add` it — it would create a broken gitlink or vendor a third-party project. | `scrapy/` |

### 5.2 Evaluation suite (D)

| Claimed metric | File | What it actually does |
|---|---|---|
| WER < 5 % | `asr-service/tests/integration/test_wer.py` | posts a dummy WAV, asserts JSON keys |
| Schema F1 > 0.90 | `nlp-service/tests/integration/test_schema_f1.py` | 4 endpoint smoke tests |
| WCAG pass rate | `tests/e2e/test_wcag_compliance.py` | **0 bytes** |
| Core Web Vitals | `tests/e2e/test_lighthouse_ci.py` | **0 bytes** |
| TTL < 5 min | `tests/e2e/test_ttl_stopwatch.py` | **0 bytes** |
| Repair latency | `qa-service/tests/integration/test_repair_latency.py` | **0 bytes** |
| Golden regression | `tests/eval/golden_regression_eval.py` | prints one line per case, then "completed successfully"; **no assertions, never calls the pipeline** |
| E2E prompt pipeline | `tests/e2e/test_prompt_pipeline.py` | **FAILS** — `render()` → `_PAGE_SHELL.format()` raises `ValueError: unexpected '{' in field name`; the template path also raises `UndefinedError: 'colors' is undefined` when called directly |
| Flutter widget test | `voicefront/test/widget_test.dart` | **does not compile** — references `MyApp`; asserts a counter UI that does not exist |
| QA service unit tests | `qa-service/tests/unit/*` | 13 pass in ~1.7 s — but against a `FakePage`, so they prove mapping logic, not browser behaviour |
| Publish tests | `publish-service/tests/test_s3_uploader.py` | collection error — `boto3` not installed |

Actual collected test count under `tests/`: **1**, and it fails. "22/22 tests passing" (`IMPLEMENTATION_COMPLETE.md`) counts per-service endpoint smoke tests only. In the report this must be phrased as **endpoint conformance**, not accuracy.

Also: `pytest.ini` sets no `testpaths`, so a bare `pytest` from the root will recurse into `scrapy/` and `.venv/`.

### 5.3 Documentation integrity (D)

- `docs/UPDATES.md` describes three features; one (template switching) **does not exist**, one (imagery) points at missing assets.
- `docs/DECK_CHANGES_v2.md` and `PROJECT_REPORT_BE.md` §4.5 both say repair is unwired — **stale** as of this tree.
- `IMPLEMENTATION_COMPLETE.md` claims 5 screens and 25 components; the app is now chat-only (with 5 orphaned screens) and the library has 84 files that collapse to 28 unique bodies.
- `settings_drawer.dart:49` tells the user "all 4 microservices … ports 8001-8004"; there are five.
- `preview_qa_screen.dart` presents fabricated QA numbers: **"99.2%" compliance, "1.2s" repair latency, "0 Critical", "2 Warnings" (one row rendered)**. Never show this to a panel.
- `README.md` is 0 bytes. There is no `CLAUDE.md`.
- `PROJECT_REPORT_BE.md` is genuinely excellent and honest — it is the only doc that grades the system the way this audit does.

---

### 5.4 Backend defects (second-pass audit)

| Service | Finding | Impact |
|---|---|---|
| **layout** | Autoescape off for `.jinja2`; JSON-LD `<script>` breakout unescaped | **Stored XSS from voice/LLM text into published pages** — the highest-severity issue in the repo |
| **layout** | Fallback shell crashes on JS braces; `price=None` raises before it | Every render failure becomes a 500, not a degraded page |
| **layout** | `LAYOUT_TEMPLATE_DIR` empty in `.env.example` | Following the docs breaks rendering — the templates-path mismatch the 2026-10-11 audit flagged is still live |
| **layout** | Dockerfile never runs `playwright install` | `/v1/layout/scrape` cannot work in the container |
| **layout** | `subprocess.run` inside `async def` (55 s) | Blocks the event loop per scrape |
| **qa** | `auto_repair` re-detects but **never returns or persists the repaired HTML** | The "repair" has no downstream effect; publish re-reads the original fixture |
| **qa** | All `QaViolationError`s map to **500**, including `QA_INVALID_REQUEST` | A 400 is reported as a server fault |
| **qa** | `page.set_content(...)` loads caller-supplied remote subresources | QA host fetches third-party URLs; nondeterministic offline |
| **asr** | Any Groq failure after retries returns the **canned transcript with HTTP 200** | A real API outage silently fabricates menu content downstream — data integrity, not just availability |
| **asr** | `MAX_FILE_SIZE_BYTES` defined but never enforced; `await file.read()` is unbounded | Memory exhaustion per request |
| **asr** | tenacity retries **every** exception, including 401/400 | Wastes quota on auth failures |
| **nlp** | Failure path hardcodes `category=food`; nested 2×3 retries = up to 6 calls | An apparel shop with a bad LLM response gets the food template |
| **nlp** | Tagline heuristic mixes a character index with word slicing (`schema_builder.py:93-98`) | Garbage tagline |
| **nlp** | `GROQ_MODEL` is shown in `/health` but not passed to the call | Misleading health output |
| **publish** | Returned `live_url` is `https://{domain}/{slug}` but the object is uploaded to `storefronts/{version_id}/index.html` | Even with a working CDN the URL 404s unless rewritten |
| **publish** | No CORS (the other four services have it); `PublishError` always maps to 409 | Inconsistent API surface |
| **all** | No `.dockerignore`; QA image would copy `.venv` | Bloated images |
| **all** | Two distinct `QaViolationError` / `PublishError` classes when `common_utils` is not importable | The handler in `main.py` will not catch the class raised by the router |

---

## 6. What more can be done — prioritised backlog

### P0 — correctness/security fixes (hours each, demo-safe)
1. **Rotate the four Groq keys** in `.env`; unify the name to `GROQ_API_KEY` and load it explicitly (`python-dotenv` or compose `env_file`). Today the keys are on disk *and* unused.
2. **Fix `_PAGE_SHELL`:** escape the JS braces (`{{`/`}}`) or move the script out of the `.format()` string. Without this, every template failure is a 500 and the E2E test fails. Add a regression test.
3. **Escape JSON-LD properly** — `json.dumps` + `.replace("</", "<\\/")`; test with `description: "</script><script>alert(1)</script>"`.
4. **Reject unsafe `version_id`** — allow `^[A-Za-z0-9_-]+$`; resolve paths with `.resolve()` and assert containment.
5. **Guard `/scrape`** — scheme allow-list, block private IP ranges, size cap, per-IP rate limit; or put it behind an internal token.
6. **Fix all five templates:** `lang="en"`, `location.raw_text` → `location.address/city`, and price formatting that tolerates `None`/strings.
7. **Make repair DOM-anchored:** re-render the page, not string-replace; or restrict the model to one node's patch and apply it once.
8. **Make `passed` meaningful:** define passing as "no critical violations", not "zero violations everywhere".
9. **Flutter build blockers:** fix `widget_test.dart` (`VoiceFrontApp`), regenerate `pubspec.lock`, add `INTERNET` + a cleartext/network-security config to the **main** manifest, and commit the 7 untracked lib files.
10. **QA service import failure:** add `httpx` to `services/qa-service/requirements.txt`; the auto-repair path cannot import today.
11. **Fix the logging formatter:** all four services format `%(request_id)s`, but no `logging.Filter` supplies it — any log record without `extra={"request_id":…}` (including uvicorn's own) raises `KeyError` during formatting. Add a filter with a default, or stop logging structured JSON with `basicConfig`.
12. **Repair loop:** apply each patch to its own section or merge results; today only the last violation's patch is kept.

### P1 — close the demo loop (1–3 days each)
10. **Flutter → QA:** call `/v1/qa/run` with `html`, render a real report screen; delete the fabricated numbers in `preview_qa_screen.dart`.
11. **Chat edits re-render:** after `set_hours` / `set_theme`, re-call layout and refresh the preview; remove `theme`/`banner` or add them to the schema.
12. **Publish path:** add `publish-service` Dockerfile + compose entry; replace `_server_side_qa_passed_check` with an in-process QA re-run before upload (no Postgres needed). Make the client's Publish button call it.
13. **Asset pipeline:** commit the `assets/` SVGs or switch to an inline SVG data-URI placeholder so no generated page has broken images.
14. **Template selection actually chooses:** use `component_picker` to assemble pages from the variant library, keeping the shell as fallback. The 84 files collapse to **28 unique bodies** (20 heroes share one, 15 navs share one) — deduplicate before claiming "84 variants".
15. **Reconnect or delete the orphan screens:** either route Home → Record → Review → Preview → QA from `main.dart`, or remove ~1,150 dead lines. Right now they misrepresent the app.

### P2 — evaluation and credibility (2–4 days)
16. **Build or delete the five evaluation scripts** the docs name (`test_wer`, `test_schema_f1`, `test_wcag_compliance`, `test_lighthouse_ci`, `test_ttl_stopwatch`). Four are 0 bytes; empty files are worse than absent ones because they imply coverage.
17. **Fix `test_prompt_pipeline.py`** and add `testpaths` to `pytest.ini` so a root `pytest` doesn't walk into `scrapy/` and `.venv/`.
18. **Golden prompt set** (S1–S6 from `07_…` §8) with assertions and a results-table generator for Chapter 4.
19. **CI (GitHub Actions):** lint + unit + contract tests; Playwright tests in the QA container; publish the results table as a build artefact.

### P3 — capability and scale (weeks)
20. **Persistence:** SQLite/Postgres for specs, versions, QA reports; turns "My Storefronts" from memory to reality.
21. **Real multilingual voice:** `record` + `permission_handler`, `/v1/asr/transcribe`, and language detection from Whisper's own `language` field — a small change that upgrades "English-only" honestly.
22. **SORT/LEARN:** failure-frequency ranking from stored QA reports; a patch store keyed by rule ID is enough before FAISS.
23. **Next.js web dashboard:** `apps/web` is four empty pages plus a 0-byte Dockerfile; recreating chat + preview in React with the existing `api-client` is the natural browser story for the viva.
24. **Auth and quotas:** API key per client; per-key rate limit protects the shared Groq quota.
25. **Schema versioning:** add `schema_version` to `StorefrontSpec`; ratify operative leniency as v1.1 (decision D7).
26. **Housekeeping:** `.dockerignore`, non-root `USER` in Dockerfiles, `curl` in the slim images (or `wget` healthchecks), `README.md`, `CLAUDE.md`, remove `docs.zip` and the binary deliverables from the repo root.

---

## 7. Skills worth invoking on this project

| Skill | Where it helps | Concrete trigger |
|---|---|---|
| **`frontend-design`** | Flutter chat/preview polish and the empty `apps/web` dashboard | "Redesign the QA report screen" / "build the Next.js dashboard" — gives typography, layout and colour direction instead of default Material. |
| **`dataviz`** | The pipeline visualizer, the QA severity charts, Chapter 4 figures | Any chart of violations-by-severity/category/viewport; the deck's bar chart (currently a corrupted screenshot). |
| **`code-review`** | The uncommitted diff in this tree | `code-review high` on the renderer/QA changes catches the repair-overwrite and template bugs. |
| **`security-review`** | P0 items 1–3 | Run on the branch after fixes; it will verify traversal, XSS and SSRF are actually closed. |
| **`simplify`** | `renderer.py` (two rendering paths collapsed into one + fallback), duplicated `main.py` middleware | Cleans reuse/altitude without changing behaviour. |
| **`docx`** | The report template | Turn `PROJECT_REPORT_BE.md` into the submitted `.docx` with correct styles; fix the T.E./B.E. mismatch flagged in `DECK_CHANGES_v2.md`. |
| **`pptx`** | `VoiceStorefront_v2 (1).pptx` | Apply the 12 slide fixes in `DECK_CHANGES_v2.md` natively, then re-export the PDF. |
| **`xlsx`** | `VoiceFront_Store_Budget_Plan.xlsx` | Rebuild the broken budget chart natively. |
| **`init`** | Missing `CLAUDE.md` | Generate a repo guide so future sessions stop re-deriving the architecture. |
| **`claude-api`** | If any model IDs/pricing appear in docs | Keep model references accurate if the project later uses Anthropic models. |

Recommended pairing: **`frontend-design` + `dataviz`** for the visual uplift, **`code-review` + `security-review`** before committing this working tree, **`pptx` + `docx`** for the submission artefacts.

---

## 8. Bottom line

The project's **engineering core is sound and genuinely demoable**: prompt → validated spec → rendered page → real browser accessibility report. It deserves credit for the NLP fallback design, the constrained extraction loop, and a real axe-core pipeline.

What it does **not** yet deserve is the production narrative in `MASTER_PLAN_V2_FINAL.md` ("90 % complete", "production-ready"). The honest position — the one already written in `PROJECT_REPORT_BE.md` — is: *semester 1 delivered an English prompt-to-storefront pipeline with detect-and-report QA; repair is now wired experimentally; repair learning, multilingual voice, persistence and CDN publishing are designed and deferred.*

Fixing P0 and P1 above (roughly **one focused week**) would move the overall grade from **C+ (69 %)** to **A− (>85 %)** without adding a single new feature — because every gap is wiring, safety, or honesty, not capability.

Three things to do before anything else:
1. **Rotate the Groq keys** and decide whether the repo's `.env` is meant to load at all.
2. **Fix `_PAGE_SHELL`** — the layout service currently cannot fall back, and its E2E test fails because of it.
3. **Commit the Flutter app** — 7 files that make it run exist only in this working tree.

> **Audit note:** two background audits ran verification scripts during this review. `tools/generate_visualizer.py` and `tools/provenance_report.py` rewrote `docs/procedure/pipeline-visualizer.html` and `data/provenance-report.html`, which were already modified before the audit began. Their pre-audit contents are not recoverable from git (HEAD differs); see `CHANGELOG_2026-10-18.md` §7.
