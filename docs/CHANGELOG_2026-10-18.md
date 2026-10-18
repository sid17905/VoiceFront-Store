# VoiceFront-Store — Latest Changes Log

**Date:** 2026-10-18
**Scope:** working tree vs `HEAD` (`2428a6f`), plus untracked assets.
**Method:** direct diff inspection (`git diff`, file reads). Nothing in the repo was modified to produce this document.

> This file records *what changed*, not whether it is correct. Correctness findings and grades live in
> [`AUDIT_2026-10-18_GRADED.md`](AUDIT_2026-10-18_GRADED.md).

---

## 0. Headline

| Area | Change in this working tree |
|---|---|
| **QA repair** | `/v1/qa/run` now calls `repair_violations()` when `auto_repair=true`, re-runs DETECT and reports `repaired_count` / `avg_repair_latency_ms` (`services/qa-service/routers/qa.py:115-126`). This **contradicts** `docs/DECK_CHANGES_v2.md` §5 and `docs/PROJECT_REPORT_BE.md` §4.5, which still say repair is unwired. |
| **Layout renderer** | Rewritten as a single mobile-first page shell with hero imagery, thumbnails and inline audit JS (`services/layout-service/core/renderer.py`). The old per-category component-assembly path was removed; `render_components()` is now a passthrough to `render()` (line 414-419). |
| **Flutter** | `main.dart` reduced to a chat-only shell; `storefronts_screen.dart` and `app_theme.dart` reworked for Material 3 colour roles and dark mode; `review_edit_screen.dart` gains a custom-image field. |
| **Component library** | +59 untracked scraped variants (nav/hero/product_grid/contact). Library totals now **84 APPROVED variants** across 4 section types. |
| **Infra** | Terraform and docker-compose modified (see §4). |
| **Docs/deck artefacts** | `T.E.-Project-Report-25-26.docx`, both deck files, and the budget spreadsheet are untracked at repo root. |

---

## 1. Backend services

### 1.1 `qa-service` — repair loop wired
- `routers/qa.py`
  - New `auto_repair: bool = False` on `QaRunRequest` (line 51).
  - When true and violations exist: imports `repair_violations`, applies each returned `repaired_html` to the page, then **re-detects** (lines 115-126).
  - Response gains `repaired_count` and `avg_repair_latency_ms`; `status` becomes `PASSED | REPAIRED | FAILED` (line 131).
- `core/repair_engine.py` — replaced stub with an LLM call to Groq (`llama-3.3-70b-versatile`) via `httpx.post`, plus a two-line heuristic fallback when no key (`replace('alt=""', …)`, `replace('href=""', …)`).
- ⚠️ **Risk introduced:** repairs are applied by string-replacing the *entire HTML document* once per violation (`repair_violations(violations, html)` at `routers/qa.py:118`; `repair_engine.py:69-70`). With N violations the LLM may return a whole rewritten page, and successive replacements overwrite each other. Repair can silently corrupt the bundle rather than patch it.
- `requirements.txt` — `+2` lines (now includes `tenacity`, `pytest-mock`).
- `tests/unit/test_stub_engines.py` — adjusted for the newly wired repair engine.

### 1.2 `asr-service`
- `main.py`, `routers/transcribe.py`, `core/{validation,normalize,whisper_engine}.py`, `tests/integration/test_wer.py` all rewritten/extended.
- Behaviour: real Groq `whisper-large-v3` when `GROQ_API_KEY` is set; otherwise returns the hardcoded "Tony's Pizza Kitchen" simulator transcript (`core/whisper_engine.py:14-23,34-36`).
- `core/language_detect.py` still returns `default` ("en") unconditionally.
- The test named `test_wer.py` still does not compute WER — it posts a dummy WAV and asserts the response shape.

### 1.3 `nlp-service`
- `core/schema_builder.py` (195 lines) — Groq Llama-3.3-70B, `response_format=json_object`, temperature 0.1, two attempts with validation-error re-prompt, regex + keyword fallback with `source: "fallback"`.
- `routers/extract.py` still accepts `prompt | transcript`, returns `NlpExtractResponse`.
- `core/ner_model.py` remains a regex compatibility shim, unused in the extract path.

### 1.4 `layout-service`
- `core/renderer.py` — the largest change (≈519 lines touched).
  - Removed: component-assembly path, `nav_html`/`hero_html`/`contact_html` slots in the page shell.
  - Added: `.mobile-container` shell (max-width 480 px), gradient app bar, hero section with Unsplash background, 72 px product thumbnails, sticky WhatsApp CTA, inline `JSON-LD`, and a `MutationObserver` that logs missing `alt` attributes.
  - `_build_context()` supplies `hero_image` from hardcoded Unsplash URLs per category (lines 281-287) and a default WhatsApp number `9876543210` (line 295).
  - `_resolve_image_url()` returns local `assets/<category>/*.svg` paths, but **no `assets/` directory exists in the repo** → broken image sources in generated pages.
- `routers/generate.py`, `main.py` updated; `/health` now reports `templates_available` and `components_available`.
- `tests/test_all_categories.py`, `tests/test_layout_service.py` adjusted.

### 1.5 `publish-service`
- Unchanged in this tree. `_server_side_qa_passed_check()` still returns `True` unconditionally (`routers/publish.py:49-59`), so the "never trust the client" gate is present in shape but not in effect.

---

## 2. Flutter app (`voicefront/`)

| File | Change |
|---|---|
| `lib/main.dart` | Reduced from ~212 to 71 lines. `MainShell` now hosts only `ChatScreen` plus a drawer and a "New Chat" action; the previous bottom-nav / multi-screen shell is gone. |
| `lib/screens/storefronts_screen.dart` | 176 lines reworked: hardcoded `AppColors` replaced with `Theme.of(context).colorScheme` roles (`onSurface`, `primary`, `surfaceContainerHighest`); adds a "Demo data preview" banner. |
| `lib/theme/app_theme.dart` | 94 lines changed: `ColorScheme.fromSeed` (Material 3) for light and dark, `GoogleFonts.interTextTheme`. |
| `lib/screens/review_edit_screen.dart` | Adds `customImageController` and a "Custom Product Image URL / Previous Asset" field (unused by any downstream call). |
| `pubspec.yaml` | Adds `flutter_markdown`; keeps `webview_flutter`, `flutter_tts`, `google_fonts`, `http`. |

Still true after these changes:
- Backend calls point at `http://10.0.2.2:800{2,3}` with no configurable base URL (`lib/services/voicefront_backend_service.dart:5-6`).
- Client-side heuristic fallbacks invent a price of `499`, a WhatsApp number `9876543210`, and a generic product name (`voicefront_backend_service.dart:20-24,40-51,73-86`).
- QA is never called from the app (`qaViolations: 0` is hardcoded at `screens/chat_screen.dart:207`).
- `onPublish: () {}` is a no-op (`chat_screen.dart:291`).
- Chat "edits" are applied by mutating the local map only — `set_hours`, `set_theme`, `add_banner` change nothing in the rendered HTML (`chat_screen.dart:122-141`).
- `AccountManager` is in-memory static demo data (`services/account_manager.dart`).

---

## 3. Data & assets

- **+59 untracked component-library files**, all `review_status: "APPROVED"`:
  - `nav` +12 → 22 total
  - `hero` +17 → 26 total
  - `product_grid` +9 → 19 total
  - `contact` +11 → 17 total
  - Total **84** variants across categories: services 24, pharmacy 18, electronics 15, food 14, apparel 13.
- Every new file traces to a real commercial site (`myntra`, `hm`, `flipkart`, `apollo247`, `sulekha`, …) with provenance blocks.
- ⚠️ The expanded library is **not consumed** by the renderer — `render_components()` ignores its `components` argument (`services/layout-service/core/renderer.py:414-419`). Passing tests therefore prove nothing about the library.

---

## 4. Infrastructure

- `infra/docker/docker-compose.dev.yml` — modified; still 4 services (asr 8001, nlp 8002, layout 8003, qa 8004). `publish-service` is still absent.
- `infra/terraform/{main,s3_cloudfront,variables}.tf` — modified. `main.tf` declares only the AWS provider (Terraform ≥1.0, provider ~>5.0). `s3_cloudfront.tf` declares an S3 bucket, a public-access-block resource with **all four blocks disabled**, and a bucket policy granting public `s3:GetObject` on `storefronts/*`. No CloudFront distribution is declared despite the filename.
- `infra/ci-cd/` still contains only `.gitkeep`.
- **0-byte files that block deployment:** `services/publish-service/Dockerfile` and `apps/web/Dockerfile`; also `infra/terraform/{ec2,rds,elasticache,networking}.tf`.
- `publish-service` cannot be composed (no Dockerfile, no compose entry).
- All four compose healthchecks call `curl`, which is not installed in the `python:3.12-slim` images → those containers will report unhealthy permanently.
- The compose build context is the repo root with no `.dockerignore`, so every build ships `node_modules/`, `.venv/`, `docs.zip` (49.8 MB) and the deck binaries.

---

## 5. Documentation and artefacts

- `docs/procedure/pipeline-visualizer.html` — **regenerated during this audit** (see §7); now 145 KB, embeds 84 components, and polls `http://127.0.0.1:8099`. The services run on **8003**, so the "Layout Service Offline" banner will show unless someone runs a server on 8099.
- `docs/pipeline-visualizer.html` is a 302-byte `<meta refresh>` redirect.
- `data/provenance-report.html` — **regenerated during this audit** (see §7); now 207 KB and lists 84 components.
- Untracked at root: `T.E.-Project-Report-25-26.docx`, `VoiceStorefront_v2 (1).pptx`, `VoiceStorefront_v2 (2).pdf`, `docs/VoiceFront_Store_Budget_Plan.xlsx`, `docs.zip` (49.8 MB).
- `docs/UPDATES.md` claims three features (chat feedback loop, dynamic imagery, template switching). Only the first and (partially) the second are real; **there is no template-switching code** in the NLP router or elsewhere.

---

## 6. Files that should not be committed as-is

| Path | Why |
|---|---|
| `docs.zip` (49.8 MB) | Archive artefact at repo root; duplicates `docs/`. |
| `services/qa-service/.venv/` | Installed virtualenv; already covered by `.gitignore`, confirm it is not staged. |
| `voicefront/build/` | Flutter build output; gitignored, confirm. |
| Root `*.docx`, `*.pptx`, `*.pdf`, `*.xlsx` | Binary deliverables; keep out of source history unless the team wants versioned reports. |
| `.env` | Contains `GROQ_API_KEYS` — correctly untracked today; never `git add -f` it. Keys should be rotated. |
| `apps/web/.env.local` | **Tracked** despite matching `.gitignore`; 0 bytes today. Remove from the index. |
| `opencode.json` | Contains a dummy local API key (`sk_omniroute`) and references a third-party model proxy. Not part of the project; remove or keep out of the repo. |
| `temp_fresh/` | Scaffold leftover, already gitignored. |

---

## 7. Audit disclosures — files rewritten by verification scripts

Two read-only background audits were run. One of them executed the two offline generators to verify they work. **Both rewrote files that were already modified before this audit session began:**

| File | Before | After | Notes |
|---|---|---|---|
| `docs/procedure/pipeline-visualizer.html` | 64,131 bytes (your uncommitted version) | 145,781 bytes | Embedded components 25 → 84; git diff vs HEAD is +1,025 lines |
| `data/provenance-report.html` | 28,270 bytes (your uncommitted version) | 207,391 bytes | Components 11 → 84; diff vs HEAD +2,207 lines |

Your pre-audit versions are **not recoverable from git**, because HEAD holds yet another (older) revision. `git checkout -- <file>` restores HEAD, not your edits. If those edits mattered, recover them from your editor's local history. The generator output is a superset of the library, so the practical loss is any hand-editing you had done to either HTML file.

---

## 8. Diff totals and commit hygiene

```
52 tracked files changed, 5,280 insertions(+), 704 deletions(-)
+59 untracked component-library JSON files (84 total; 28 unique HTML bodies)
+7 untracked binary/document artefacts at repo root
+7 untracked Flutter lib files (the runnable chat app exists only in the working tree)
```

**Line-ending churn:** the working tree is CRLF while HEAD is LF, and there is no `.gitattributes`. Dozens of platform files (`android/`, `ios/`, `linux/`, `macos/`, `windows/`, `test/widget_test.dart`, `analysis_options.yaml`) show as modified with **zero semantic change**. Before committing, either add `* text=auto eol=lf` to `.gitattributes` and renormalise, or `git checkout --` the untouched scaffolding so the commit isn't 40 files of line endings.

**Never commit:**

1. `scrapy/` — a 42 MB nested clone of upstream Scrapy **with its own `.git`**. It would create a broken gitlink or vendor a third-party project.
2. `opencode.json` — machine-local model-router config with a dummy key.
3. `.env` — holds live-looking Groq keys; rotate them and keep the file ignored.
4. `services/qa-service/.venv/`, `node_modules/`, `__pycache__/`, `temp_fresh/`, `.pytest_cache/` — confirm none are staged.
5. `packages/common_utils/auth.py` — as written, ships a hard-coded fallback JWT secret and depends on packages absent from every requirements file.
6. `docs.zip` (49.8 MB) and the three presentation binaries — artefacts, not source.
