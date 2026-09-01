# Person D — Phase 0/1 deliverables (qa-service + publish-service)

Everything below maps directly to the checklist in `person_d_qa_publish.md`. Copy the
`services/qa-service/`, `services/publish-service/`, `data/constraint-rules/`,
`data/seed/rendered_bundles/`, and `packages/common-utils/` folders into your repo at the
matching paths from `files.md`.

## What's built and verified working

| Checklist item | File(s) | Status |
|---|---|---|
| 15–20 constraint rules | `data/constraint-rules/*.json` (18 rules) | Done — 10 axe-core-backed WCAG checks, 8 hand-authored structural checks |
| Playwright renders at 5 viewports | `core/detect_engine.py` | Code complete — **not runnable in this sandbox** (see Known limitation below), will work on your laptops |
| `detect_engine.py` (no auto-repair) | `services/qa-service/core/detect_engine.py` | Done, unit-tested with a fake Playwright page |
| Stub `sort_engine.py` / `repair_engine.py` / `learn_engine.py` | `services/qa-service/core/*.py` | Done — documented pass-throughs with Phase 3/4 TODOs written in as docstrings |
| `s3_uploader.py` | `services/publish-service/core/s3_uploader.py` | Done, unit-tested with mocked boto3 — **run the real dev-bucket smoke test yourself** (see below), that part needs live AWS creds I don't have |
| `routers/qa.py`, `routers/publish.py`, `main.py` | both services | Done, wired to `api_contracts.md` shapes exactly, boot-tested with FastAPI's TestClient |

**All 20 tests pass** (13 in qa-service, 7 in publish-service) — I actually ran them, not just wrote them. Run them yourself:

```bash
cd services/qa-service && pip install -r requirements.txt && pytest -v
cd services/publish-service && pip install -r requirements.txt && pytest -v
```

## Known limitation: I couldn't run a real browser here

This sandbox's network is locked to a small allowlist (pypi, npm, github, etc.) — it doesn't
include Playwright's browser-download CDN or `axe-core`'s CDN fallback, and I have no AWS
credentials. So:

- `detect_engine.py`'s unit tests use a **fake Playwright page** (`FakePage` in
  `test_detect_engine.py`) — this proves the axe-result-mapping and custom-check logic is
  correct, but it has never rendered a real page in a real browser.
- I did **not** run it against `data/seed/rendered_bundles/fixture-good.html` /
  `fixture-bad.html` with a real Chromium instance. Do that first thing once you have this on
  your machine — it's the single most important "does this actually work" check:

```bash
cd services/qa-service
npm install axe-core          # detect_engine.py expects node_modules/axe-core/axe.min.js
playwright install chromium   # downloads the browser binary
python core/detect_engine.py ../../data/seed/rendered_bundles/fixture-bad.html
# expect ~6-7 violations: overflow, broken image, duplicate id, empty link,
# tiny tap target, low contrast, missing viewport meta, missing lang attr, missing title
python core/detect_engine.py ../../data/seed/rendered_bundles/fixture-good.html
# expect 0 or very few violations
```

- `s3_uploader.py`'s tests mock `boto3` entirely. The Phase 1 checklist also asks you to
  "confirm a file uploads and is publicly readable only at the intended prefix" against a
  **real** dev S3 bucket — I can't do that without credentials. Once you have a dev bucket:

```bash
export PUBLISH_S3_BUCKET=your-dev-bucket
export PUBLISH_AWS_REGION=ap-south-1
python -c "
from core.s3_uploader import upload_bundle, verify_prefix_isolation
print(upload_bundle('<h1>test</h1>', 'smoke-test'))
print('prefix isolation check:', verify_prefix_isolation())
"
```
Then also **write the actual bucket policy** restricting public read to `storefronts/*` — that's
a Terraform/console task (`infra/terraform/s3_cloudfront.tf`), not something this Python file can
enforce by itself. The code assumes the policy exists; it doesn't create it.

## A bug I found and fixed while testing

`wait_for_invalidation()` originally had `timeout_sec: int = _INVALIDATION_TIMEOUT_SEC` as a
default argument — Python binds default arguments once, at function-definition time, not per
call. That meant overriding `_INVALIDATION_TIMEOUT_SEC` later (via env config or a test
monkeypatch) silently did nothing, and the very first test run of the "invalidation never
completes" case genuinely hung for 60 seconds before failing correctly. Fixed by resolving the
default inside the function body instead. Worth remembering for any other module-level constant
you use as a default arg elsewhere in the codebase.

## Deliberately NOT built yet (Phase 3/4, not Phase 1 scope)

- `sort_engine.py`'s real failure-probability ranking (Phase 3, `procedure_plan.md` step 55).
- `repair_engine.py`'s FAISS lookup + Groq-hosted LLM-assisted repair fallback (Phase 4, steps 65–67).
- `learn_engine.py`'s actual FAISS writes (Phase 4, step 68) — there's nothing to learn from until repair exists.
- Real `storefront_versions`/`qa_reports` Postgres lookups in both routers — right now `qa/run`
  and `publish` both resolve bundles against local seed fixtures
  (`data/seed/rendered_bundles/{version_id}.html`), per the exact mitigation
  `milestones.md`'s risk section calls out: validate against static fixtures, don't wait on
  Track C. Swap this for a real DB lookup once layout-service is producing real output (Phase 2).
- `publish.py`'s server-side `qa_report.passed` re-check is stubbed to always return `True` for
  the same reason — the `qa_reports` table doesn't exist yet. The shape (never trust the client)
  is correct now; the data source needs to change in Phase 2+.

## One thing worth flagging to the team now

`packages/common-utils/` (hyphen) isn't directly importable as a Python package —
`from common_utils.exceptions import X` needs a valid identifier, and `common-utils` isn't one.
I worked around it locally with a symlink (`packages/common_utils -> common-utils`), and every
`core/*.py` file also has a try/except fallback so the code still runs even without the symlink.
Decide as a team whether the symlink approach is fine to commit, or whether you'd rather rename
the folder / use a proper `pyproject.toml` package mapping — small decision, but better made once
by the whole team than differently by each service.
