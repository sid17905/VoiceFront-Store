# VoiceFront-Store — Remediation Plan to A+ (All Phases)

**Created:** 2026-10-18
**Baseline:** `docs/AUDIT_2026-10-18_GRADED.md` (overall C+ ≈ 68 %)
**Goal:** every graded area at **A+**, with measured evidence rather than claims.
**Rule of this plan:** a step is done only when its **Proof** command passes on a clean checkout.

---

## 0. What "A+" means here (and what it cannot mean)

A+ is defined by **gates**, not adjectives. Every gate is observable in CI or by one command.

| Phase | A+ gate |
|---|---|
| **P1 ASR** | Real audio end-to-end; WER measured on a committed benchmark set; no fabricated transcript can reach a caller without an explicit `mode: "simulator"` field; 503 on upstream failure; upload limits enforced |
| **P2 NLP** | Schema-validity rate and field-level F1 measured on a committed gold set; fallback never invents a category; contract matches `api_contracts.md` |
| **P3 Layout** | All five categories render category-correct pages from **their own templates**; output is XSS-safe under adversarial input; valid JSON-LD; no broken assets; no `None`-price crash; component library actually used |
| **P4 QA** | Real browser DETECT; repairs are node-anchored, verified by re-detection, persisted and returned; SORT ranks by measured failure frequency; LEARN stores only confirmed patches; WCAG pass rate measured |
| **P5 Publish** | Deployable container; refuses to publish unless QA re-passes **server-side**; URL matches the uploaded object; CloudFront + OAC declared; live URL demonstrable |
| **Client** | Release build reaches the backend; QA report is real; edits re-render; publish works; accessibility and dark mode correct; tests compile and pass |
| **Security** | No secret in the tree; no unescaped sink; no SSRF/traversal; auth + rate limits on mutating/expensive routes; pinned dependencies |
| **Testing** | Every metric in `testing.md` has a runnable script; CI green; coverage thresholds per service |
| **Docs** | Every claim in README/report/deck is reproducible from the repo |

**What A+ cannot mean:** "zero vulnerabilities." No codebase earns that. A+ here means *no known defect in the audit remains unaddressed, and the process catches regressions automatically.* State it that way in the viva.

---

## 1. Guardrails before touching code

| Step | Action | Why |
|---|---|---|
| **G1** | **Rotate the four Groq keys** in `.env` at console.groq.com. Create one key for dev, one for CI. | The current keys are on disk and were read by tooling. Rotation is the only real fix. |
| **G2** | Create branch `audit-fixes`. Do **not** fix on `main`. | Every step below is reviewable as a PR. |
| **G3** | Back up the working tree: `git stash push -u -m "pre-remediation"` **or** copy `F:\VoiceFront-Store` to a sibling folder. | The tree contains uncommitted work, including 7 untracked Flutter files and two generated HTML reports. A stash is not enough if something goes wrong mid-sequence. |
| **G4** | Add `.gitattributes` and normalise line endings (see step **D3**). Do this **first**. | Otherwise every diff below is buried in CRLF noise and you cannot review it. |
| **G5** | Commit the current tree as-is (after G3/G4) on `audit-fixes` — even the imperfect state. | You need a revert point that is *yours*, not HEAD. |

**Proof:** `git log --oneline -1` shows a commit on `audit-fixes`; `git status` is clean.

---

## 2. Phase S — Security (blocking everything else)

> Order matters. S1–S4 are the stored-XSS and injection class; they make the system safe to expose at all.

### S1. Turn escaping on for Jinja templates
**File:** `services/layout-service/core/renderer.py:22-27`

```python
from jinja2 import Environment, FileSystemLoader

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,          # escape every template, including .jinja2
    trim_blocks=True,
    lstrip_blocks=True,
)
```

**Why:** `select_autoescape(["html"])` leaves `.jinja2` unescaped; `shop_name`/`description`/product text reach the page raw.
**Failure modes to test:**
- `<script>alert(1)</script>` in `shop_name` → appears as `&lt;script&gt;`.
- `"` in `description` inside an attribute → `&quot;`.
- `&` → `&amp;` (not double-escaped in JSON-LD — see S2).
**Proof:** `pytest services/layout-service/tests/test_xss.py -q` (new test, below).

```python
# services/layout-service/tests/test_xss.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from core.renderer import render
from core.palette_engine import get_palette

def test_injection_is_escaped():
    spec = {
        "shop_name": '<script>alert(1)</script>',
        "category": "food",
        "description": '"><img src=x onerror=alert(1)>',
        "products": [{"name": "<b>x</b>", "price": 10, "currency": "INR"}],
        "hours": [], "contact": {}, "location": None,
    }
    html = render("food", spec, get_palette("food"))
    assert "<script>alert(1)</script>" not in html
    assert "onerror=alert(1)" not in html or "&quot;" in html
```

### S2. Build JSON-LD in Python, escape script context
**Files:** `services/layout-service/core/renderer.py` (`_render_json_ld`), all five `templates/*.jinja2`

1. Replace the hand-written JSON block in each template (lines ~50-69) with exactly:
   ```jinja
   {{ json_ld | safe }}
   ```
2. Pass `json_ld` in `template_ctx`.
3. In `_render_json_ld`, escape the script terminator:
   ```python
   from markupsafe import Markup
   def _render_json_ld(spec: dict) -> Markup:
       data = {...}  # unchanged fields
       payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
       return Markup(f'<script type="application/ld+json">{payload}</script>')
   ```
**Why:** `json.dumps` does not escape `</script>`; and the template JSON currently omits commas when both `location` and `contact` exist.
**Proof:** new test asserts `json.loads` succeeds for specs with/without location/contact and that `"</script>"` in `description` does not terminate the block.

### S3. Validate `version_id` everywhere it becomes a path or key
**Files:** `services/qa-service/routers/qa.py:79-89`, `services/publish-service/routers/publish.py:62-73`, `services/publish-service/core/s3_uploader.py:64-68`

Add one shared helper (put it in `packages/common_utils/validators.py`):
```python
import re
from pathlib import Path

_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

def safe_version_id(value: str) -> str:
    if not _VERSION_RE.fullmatch(value or ""):
        raise ValueError("invalid version_id")
    return value

def safe_child(base: Path, filename: str) -> Path:
    target = (base / filename).resolve()
    if base.resolve() not in target.parents:
        raise ValueError("path escapes base directory")
    return target
```
Use `safe_version_id` in both routers; use `safe_child` for the fixture read.
**Failure modes to test:** `../x`, `..\\x`, `a/b`, `a%2e%2e%2fb`, empty, 65 chars, Unicode.
**Proof:** parametrised test expecting `ValueError` for each.

### S4. Close the SSRF hole in `/v1/layout/scrape`
**File:** `services/layout-service/routers/scrape.py`

```python
import ipaddress, socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443}

def assert_safe_url(url: str) -> None:
    p = urlparse(url)
    if p.scheme not in ALLOWED_SCHEMES:
        raise ValueError("scheme not allowed")
    if p.username or p.password:
        raise ValueError("credentials in URL not allowed")
    host = p.hostname
    if not host:
        raise ValueError("missing host")
    port = p.port or (443 if p.scheme == "https" else 80)
    if port not in ALLOWED_PORTS:
        raise ValueError("port not allowed")
    for info in socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP):
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise ValueError("internal address not allowed")
```
Then:
- call `assert_safe_url` before `subprocess.run`;
- run the subprocess off the event loop: `await asyncio.to_thread(...)`;
- cap `full_element_html` and `screenshot_b64` sizes;
- return `400 SCRAPER_URL_REJECTED` (not 500) on rejection;
- optional `X-Internal-Token` header check when `SCRAPE_REQUIRE_TOKEN=1`.

**Known limitation to document:** DNS rebinding is still possible between the resolution check and the child process fetch. Mitigate by having `_playwright_worker.py` re-resolve and refuse, or run the scraper in a network namespace with egress controls. State this in the report rather than claiming the hole is fully closed.

**Proof:** tests for `file://`, `gopher://`, `http://127.0.0.1`, `http://10.0.0.1`, `http://169.254.169.254/latest/meta-data/`, `http://user:pass@example.com`, `http://example.com:22`.

### S5. Remove the browser-fingerprint script
**File:** `renderer.py:162-186`
Delete the `window.__voicefront_fingerprint` block. If the `alt` warning is wanted, do it in the QA service, not in customer pages.
**Why:** shipping a fingerprint global into every generated storefront is a privacy and trust problem with no product value.

### S6. Stop emitting invented contact data and dead asset paths
**Files:** `renderer.py:281-295`, `_resolve_image_url` at `:221-274`

- Delete the default `"9876543210"`. If `contact.whatsapp` is absent, **do not render the WhatsApp CTA** (template `{% if %}` already supports this).
- Replace Unsplash URLs with a configurable `HERO_IMAGE_BASE` env var; default to an inline SVG gradient data URI.
- Either commit the `assets/` tree or replace `_resolve_image_url` with a deterministic inline SVG placeholder:
  ```python
  def _placeholder_svg(label: str, color: str) -> str:
      return ("data:image/svg+xml;charset=utf-8,"
              + quote(f'<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144">'
                      f'<rect width="100%" height="100%" fill="{color}"/>'
                      f'<text x="50%" y="50%" text-anchor="middle" fill="#fff" '
                      f'font-family="sans-serif" font-size="14">{escape(label[:12])}</text></svg>'))
  ```
**Proof:** render a spec with no contact and assert `wa.me` is absent; render a product and assert the `src` is either a committed path that exists or a `data:` URI.

### S7. Fix the broken fallback shell
**File:** `renderer.py:29-218, 396`

Replace `_PAGE_SHELL` (a `.format()` string containing JS braces) with a real template: move it to `services/layout-service/templates/_fallback.jinja2` and render it through `_env`. Delete the `.format()` call.
**Failure modes it closes:** `ValueError: unexpected '{' in field name`; the fallback masking the original error.
**Also:** log the original exception before falling back:
```python
except Exception:
    logger.exception("template render failed; using fallback", extra={"template_id": template_id})
```
**Proof:** `pytest services/layout-service/tests/test_render.py -q` plus a test that forces a missing template and asserts a complete HTML document is returned.

### S8. Price and location formatting in Python, not Jinja
**Files:** `renderer.py`, all templates

Pre-format in `_build_context`:
```python
def _price_display(value, currency="INR"):
    if value is None or value == "":
        return "Ask for price"
    if isinstance(value, (int, float)):
        symbol = {"INR": "₹", "USD": "$", "EUR": "€"}.get(currency, currency + " ")
        return f"{symbol}{value:,.0f}"
    return str(value)          # already a string like "₹180"

def _location_display(loc):
    if not loc: return ""
    parts = [loc.get("address"), loc.get("city"), loc.get("state"), loc.get("pincode")]
    return ", ".join(p for p in parts if p)
```
Templates use `{{ product.price_display }}` and `{{ location_display }}`.
**Failure modes closed:** `TypeError` on `None` price; empty location (the templates read `location.raw_text`, which no longer exists); wrong currency for non-INR specs.

### S9. Empty `LAYOUT_TEMPLATE_DIR` must not break rendering
**File:** `renderer.py:17-20`

```python
_raw_dir = os.environ.get("LAYOUT_TEMPLATE_DIR", "").strip()
_TEMPLATE_DIR = (Path(_raw_dir) if _raw_dir
                 else Path(__file__).resolve().parents[1] / "templates")
```
**Proof:** test with `LAYOUT_TEMPLATE_DIR=""` and `"   "` both render.

### S10. Secrets and configuration hygiene
1. Unify env names: use **`GROQ_API_KEY`** everywhere; change `.env` to match (`GROQ_API_KEYS` → `GROQ_API_KEY`).
2. Load config explicitly: add `python-dotenv` to each dev requirements file and call `load_dotenv()` **only when `ENV != "production"`**; in production, fail fast if `GROQ_API_KEY` is missing.
3. `packages/common_utils/auth.py`: delete the fallback secret; require `JWT_SECRET_KEY` or raise at import. Better: delete the file until auth is actually wired (nothing imports it).
4. Remove `opencode.json` from the repo.
5. `git rm --cached apps/web/.env.local`; add it to `.gitignore` patterns already present.
**Proof:** `grep -rn "super-secret-iron-man\|sk_omniroute" --exclude-dir=.git .` returns nothing; app boots with no key and reports `"mode": "fallback"` in `/health`.

### S11. Add auth and rate limiting to mutating/expensive routes
**Files:** all five `main.py`

- Add `slowapi`:
  ```python
  from slowapi import Limiter
  from slowapi.util import get_remote_address
  limiter = Limiter(key_func=get_remote_address)
  app.state.limiter = limiter
  app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
  ```
- Decorate: `/v1/nlp/extract` 30/min, `/v1/layout/generate` 60/min, `/v1/qa/run` 10/min, `/v1/layout/scrape` 5/min, `/v1/publish` 5/min, `/v1/asr/transcribe` 10/min.
- Add a shared API-key dependency for `/v1/publish` and `/v1/layout/scrape` first (`X-API-Key`, constant-time compare). Extend to all routes when a client exists.
- Body limits: `max_length=4000` on `prompt`; reject `html` bodies over 2 MB with **413**.

### S12. Container and build hygiene
- Add `.dockerignore` at repo root:
  ```
  .git
  scrapy
  node_modules
  **/.venv
  **/__pycache__
  voicefront/build
  docs.zip
  *.docx
  *.pptx
  *.pdf
  ```
- Add non-root users to all Dockerfiles (`useradd -m app && USER app`; for the Playwright image use `pwuser`).
- Replace `curl` healthchecks with a Python one-liner so `python:3.12-slim` works:
  ```dockerfile
  HEALTHCHECK CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8003/health', timeout=3).status==200 else 1)"
  ```
- Pin base images by digest where practical.

**Phase S gate:** every S proof passes; `pip-audit` and `npm audit` run clean or have documented exceptions.

---

## 3. Phase L — Layout correctness

### L1. Make each category actually render its own template
- Keep `select_template()` as the category passthrough (it is correct for this design), but add a **template existence check** at startup and expose it in `/health`.
- Remove the catch-all that silently falls back on *any* exception. Fall back only on `jinja2.TemplateNotFound` and `jinja2.TemplateSyntaxError`; let data errors surface as `500 LAYOUT_RENDER_FAILED` with a safe message.
- Add a `template_version` string to the response so the caller can tell which template rendered.

### L2. Wire the component library into the render path
**File:** `renderer.py:414-419`, `core/component_picker.py`, `routers/generate.py`

```python
def render_components(spec, palette, components) -> str:
    env = SandboxedEnvironment(loader=BaseLoader(), autoescape=True)
    parts = {}
    for section in ("nav", "hero", "product_grid", "contact"):
        variant = components.get(section)
        if variant is None:
            return render(spec["category"], spec, palette)  # monolith fallback
        body = env.from_string(variant["html"]).render(**ctx)
        css  = env.from_string(variant.get("css", "")).render(**ctx)
        parts[section] = f"<style>{css}</style>{body}"
    return _assemble_page(spec, palette, parts)
```
- `routers/generate.py`: `comps = pick_components(spec_dict); html = render_components(spec_dict, palette, comps)`.
- Add `variant_strategy` to the request (default `"first"`, deterministic for demos).

**Why:** the 84-file library is currently dead code and the test "assembly matches manual render" is tautological.
**Proof:** a test that selects variant `food-hero-zomato`, renders, and asserts a marker string unique to that variant appears in the output — a test that would fail if `render_components` were still a passthrough.

### L3. Curate the component library
- Add `tools/dedupe_components.py`: hash `html` + `css`; for each duplicate cluster keep one, set the rest to `review_status: "DUPLICATE"`.
- Change the harvester to write `review_status: "PENDING"` by default. Only a human/CI approval step flips it to `APPROVED`.
- Reject captures whose `source_html_snippet` matches "JavaScript is disabled" or is under ~120 bytes.
- Fill the thin cells (`apparel/product_grid`, `electronics/contact`) before claiming completeness.
**Proof:** `python tools/dedupe_components.py --report` prints unique counts; a CI test asserts every `APPROVED` file has a non-duplicate body and >120 bytes.

### L4. Page-level correctness
- `lang="en"` in every template and the fallback.
- Add `description` meta, Open Graph tags, and a canonical `<title>`.
- Add a `<main>` landmark and skip link (helps the `aria-landmark` rule).
- Ensure every `<img>` has `alt` (product name or "Product image").
- Tap targets ≥ 24 px in the base CSS (already present in templates; keep it in the fallback).
**Proof:** `pytest services/layout-service/tests/test_all_categories.py` plus a snapshot test asserting required tags per category.

### L5. Dockerfile for layout-service
Add `RUN playwright install --with-deps chromium` (the scrape router needs it) or remove `playwright`/`scrapling` from requirements if scraping is deferred — **decide explicitly**, do not ship a dependency that cannot run.

---

## 4. Phase Q — QA detection and repair

### Q1. Add the missing dependency
`services/qa-service/requirements.txt` → add `httpx==0.27.2`.

### Q2. Correct HTTP codes
**File:** `routers/qa.py`, `main.py`
- `QA_INVALID_REQUEST` → **400**
- `QA_VERSION_NOT_FOUND` → **404**
- `QA_NO_RULES_LOADED`, `QA_AXE_CORE_MISSING`, `QA_DETECT_PIPELINE_FAILURE` → **500**
Implement by giving `QaViolationError` a `status_code` attribute and mapping it in the handler.

### Q3. Rewrite repair as node-anchored, deterministic first
**File:** `core/repair_engine.py` (replace the whole file)

```python
from bs4 import BeautifulSoup

DETERMINISTIC = {
    "wcag-2.2-aa-alt-text-001": _fix_alt,
    "wcag-2.2-aa-lang-attr-001": _fix_lang,
    "wcag-2.2-aa-page-title-001": _fix_title,
    "structural-empty-link-001": _fix_empty_link,
    "structural-duplicate-id-001": _fix_duplicate_ids,
    "wcag-2.2-aa-focus-visible-001": _fix_focus_css,
    "wcag-2.2-aa-target-size-001": _fix_target_css,
}

def repair_document(html: str, violations: list[Violation]) -> tuple[str, list[RepairOutcome]]:
    soup = BeautifulSoup(html, "html.parser")
    outcomes = []
    for rule_id in {v.rule_id for v in violations}:
        fixer = DETERMINISTIC.get(rule_id)
        if fixer is None:
            outcomes.append(RepairOutcome(rule_id, "manual", repaired=False))
            continue
        before = str(soup)
        fixer(soup)
        after = str(soup)
        outcomes.append(RepairOutcome(rule_id, "deterministic", repaired=after != before))
    return str(soup), outcomes
```
Rules that **cannot** be auto-fixed safely (contrast, heading order, form labels without context) are reported as `manual` — never "repaired".

**LLM path (only if you keep it):**
- send **one node's outerHTML**, not the page;
- require the response to parse as exactly one element;
- reject if the output contains `<html`/`<body` or is longer than 4× the input;
- replace only the original node;
- re-run DETECT and mark repaired only if the rule disappears.

### Q4. Apply and return repairs correctly
**File:** `routers/qa.py:113-131`

```python
if request.auto_repair and violations:
    repaired_html, outcomes = repair_document(html, violations)
    html = repaired_html
    violations = detect_violations(html)
    repaired_count = sum(1 for o in outcomes if o.repaired)
    ...
return QaRunResponse(qa_report=..., status=..., repaired_html=html if request.auto_repair else None)
```
Add `repaired_html` to `QaRunResponse` so the client and publish can use it. Per-violation `was_repaired` comes from re-detection, not from the repairer's claim.

### Q5. Make `passed` defensible
Define: `passed = no violations of severity == "critical"`. Keep `total_violations` for the report. Document the definition in `api_contracts.md` and in the response (`"pass_rule": "no-critical"`).

### Q6. Fix the inert focus check
`getComputedStyle(el, ':focus')` cannot read pseudo-class state. Replace with an injected stylesheet probe:
```js
() => {
  const probe = document.createElement('a');
  probe.href = '#'; probe.textContent = 'x';
  document.body.appendChild(probe);
  probe.focus();
  const s = getComputedStyle(probe);
  const removed = s.outlineStyle === 'none' && s.boxShadow === 'none';
  probe.remove();
  return removed;
}
```

### Q7. SORT with real data
- Persist every QA report (start with SQLite via `sqlite3`, no server needed).
- `rank_failure_risk(rules, history)` orders rules by observed failure frequency; ties preserve file order.
- Record the ranking in the response as `rules_checked` (count) so SORT is visible.

### Q8. LEARN with a real store
- After a repair survives re-detection, store `{rule_id, before_hash, patch, times_reused}` in a JSON file keyed by rule.
- On the next repair, try the stored patch first (deterministic, no LLM call). This is a legitimate "learned rule store" without FAISS; state that FAISS is deferred.

**Phase Q gate:** `test_repair_latency.py` is non-empty and measures both deterministic and LLM paths; a fixture with 6 known violations goes to 0 critical after `auto_repair`, and the returned HTML is valid and still contains the shop name.

---

## 5. Phase A — ASR

### A1. Never return fabricated content silently
**File:** `core/whisper_engine.py`

- Add `ASR_MODE` (`live` default, `simulator` explicit).
- In `live` mode, if the key is missing or Groq fails after retries → raise `AsrUnavailable`; router returns **503 `ASR_UPSTREAM_UNAVAILABLE`**.
- The simulator keeps returning the canned transcript **only** when `ASR_MODE=simulator`, and the response must include `"mode": "simulator"`.
- Add `mode` to `TranscriptionResponse`.

### A2. Enforce size and type
- `MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024`; check before `await file.read()` using `request.headers["content-length"]` when present, then re-check `len(content)` → **413**.
- Verify magic bytes: `RIFF`/`WAVE`, `ID3`, `fLaC`, `OggS`, `ftyp`; reject otherwise → **400 `ASR_UNSUPPORTED_FORMAT`**.

### A3. Retry only retryable errors
```python
retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIConnectionError))
```
Add `timeout=60.0` to the SDK call; construct one `Groq` client per process, not per attempt.

### A4. Do not block the event loop
Wrap the synchronous SDK call: `response = await asyncio.to_thread(_call_groq)`.

### A5. Real WER benchmark
- Commit `data/seed/asr_benchmark/manifest.jsonl` with `{audio, reference}` lines and at least 20 audio files (5 per category).
- `tests/integration/test_wer.py`:
  ```python
  import jiwer
  @pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="needs live ASR")
  def test_wer_below_threshold():
      results = []
      for item in load_manifest():
          out = transcribe(item["audio"])
          results.append(jiwer.wer(item["reference"], out["transcript"]))
      assert statistics.mean(results) < 0.10   # set the honest threshold from the first run
  ```
- Report the measured number in Chapter 4. If it is 8 %, say 8 %.

### A6. Language detection via Whisper
Use `response.language` from `verbose_json` to populate `language` instead of echoing the request. Keep `detect_language()` as a pre-step only if you add a real model; otherwise delete the stub and document that Whisper does the detection.

---

## 6. Phase N — NLP

### N1. Honor `GROQ_MODEL`
```python
model = model or os.getenv("GROQ_MODEL", DEFAULT_MODEL)
```
Pass it into the call and continue reporting it in `/health`.

### N2. Stop defaulting to `food`
Replace both `StoreCategory.FOOD` fallbacks with an explicit failure:
- if the heuristic cannot infer a category, return `is_valid=False` and `invalid_fields=["category"]`;
- the router still returns 200 with the spec, per contract.

### N3. Fix the tagline heuristic
`idx = prompt_lower.index("named") + 5` is a character index used on `words`. Replace with word-index logic:
```python
tokens = prompt.split()
lower = [t.lower() for t in tokens]
for marker in ("named", "called"):
    if marker in lower:
        start = lower.index(marker) + 1
        tagline = " ".join(tokens[start:start + 8])
        break
```

### N4. Bound input and align the contract
- `prompt: str = Field(..., max_length=4000)`.
- `invalid_fields` per `api_contracts.md` is `[{field, reason}]`. Either change the model to that shape (recommended) or amend the contract. Do not leave both.
- Drop `shop_id` from the request if it is ignored, or store it.

### N5. Real schema F1
- Commit `data/seed/storefront_specs/gold/*.json` for 30 prompts.
- `test_schema_f1.py` computes per-field precision/recall/F1 (shop_name exact-normalised, category exact, product name/price set match) and asserts the macro F1 threshold you actually measured.

---

## 7. Phase P — Publishing

### P1. Real server-side QA gate
**File:** `routers/publish.py`
```python
def _qa_passed(html: str) -> bool:
    r = httpx.post(f"{QA_URL}/v1/qa/run", json={"html": html}, timeout=120)
    r.raise_for_status()
    return bool(r.json()["qa_report"]["passed"])
```
- Remove `_server_side_qa_passed_check` (the always-True stub).
- Read the bundle **before** the check; refuse with `409 PUBLISH_QA_NOT_PASSED`.
- On QA service unreachable → `503`, never publish.

### P2. Make the URL match the object
Choose one and document it:
- **(a)** key `storefronts/{version_id}/index.html`, URL `https://{domain}/storefronts/{version_id}/index.html`; or
- **(b)** CloudFront Function/Origin Path rewrite `/x/` → `/storefronts/x/index.html`, URL `https://{domain}/{version_id}/`.
Option (b) is nicer; option (a) is honest with less infrastructure. Pick (a) for the demo.

### P3. Fix `verify_prefix_isolation`
Either implement a real check (HEAD the object through CloudFront and assert 403 outside the prefix) or delete the function. A test that returns `True` without testing anything is worse than no test.

### P4. Error mapping and CORS
- `PUBLISH_QA_NOT_PASSED` → 409; `PUBLISH_BUNDLE_NOT_FOUND` → 404; `PUBLISH_S3_FAILED` → 502; invalid request → 422.
- Add the same CORS middleware as the other services.

### P5. Dockerfile and compose
- Write `services/publish-service/Dockerfile` mirroring nlp-service (non-root, healthcheck).
- Add the service to `docker-compose.dev.yml` on **8005**, with `QA_URL=http://qa-service:8004`.
- Add `depends_on: [qa-service]`.

---

## 8. Phase I — Infrastructure

### I1. Compose correctness
- Remove `deploy.resources` (ignored outside Swarm) or move to `docker-compose.prod.yml` for Swarm.
- Add `env_file: ../../.env` to services that need it.
- Add `depends_on` with health conditions: nlp ← asr (optional), qa ← layout, publish ← qa.
- Add a `web` service only if `apps/web` is implemented (currently 0 bytes — see F12).

### I2. Terraform: real CloudFront + private bucket
```hcl
resource "aws_s3_bucket_public_access_block" "storefronts" {
  bucket                  = aws_s3_bucket.storefronts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "storefronts-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  default_root_object = "index.html"
  origin {
    domain_name              = aws_s3_bucket.storefronts.bucket_regional_domain_name
    origin_id                = "s3-storefronts"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }
  default_cache_behavior {
    target_origin_id       = "s3-storefronts"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    forwarded_values { query_string = false cookies { forward = "none" } }
  }
  restrictions { geo_restriction { restriction_type = "none" } }
  viewer_certificate { cloudfront_default_certificate = true }
}
```
Bucket policy becomes `Principal: cloudfront.amazonaws.com` with `AWS:SourceArn`.
**Note:** a custom domain + ACM certificate must be created in **us-east-1**; keep that as a follow-up step and say so.

### I3. Terraform quality
- Add `backend "s3" {}` (or local state + documented risk).
- Use `var.environment` in tags.
- Delete the four empty `.tf` files or fill them; empty files imply work that does not exist.

### I4. CI (the biggest single grade lever)
`.github/workflows/ci.yml`:
```yaml
name: ci
on: [push, pull_request]
jobs:
  python:
    strategy:
      matrix:
        service: [asr-service, nlp-service, layout-service, qa-service, publish-service]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.12"}
      - run: pip install -r services/${{ matrix.service }}/requirements.txt -r requirements-dev.txt
      - run: pytest services/${{ matrix.service }}/tests -q --maxfail=1
  lint:
    steps:
      - run: ruff check services packages tests
      - run: ruff format --check services packages tests
  docker:
    steps:
      - run: docker compose -f infra/docker/docker-compose.dev.yml build
  flutter:
    steps:
      - uses: subosito/flutter-action@v2
      - run: flutter pub get && flutter analyze --fatal-infos && flutter test
```
Add `requirements-dev.txt` with `ruff`, `pytest`, `pytest-asyncio`, `httpx`, `boto3`, `jiwer`, `beautifulsoup4`.
**Gate:** the workflow is green on a PR that touches each service.

---

## 9. Phase F — Flutter to A+

### F1. Commit the app and fix the build
- `git add voicefront/lib/**` (the 7 untracked files).
- Replace `test/widget_test.dart`:
  ```dart
  testWidgets('chat shell renders greeting', (tester) async {
    await tester.pumpWidget(const VoiceFrontApp());
    expect(find.textContaining('VoiceFront AI'), findsOneWidget);
  });
  ```
- Regenerate `pubspec.lock`; remove `cupertino_icons: ^2.0.0` if it does not resolve (keep 1.0.8).
- `flutter analyze --fatal-infos` clean.

### F2. Make the release build actually reach the backend
- Add to **main** `AndroidManifest.xml`: `<uses-permission android:name="android.permission.INTERNET"/>`.
- Add `android:usesCleartextTraffic="true"` **only** in `debug/` and `profile/` manifests, or add `network_security_config.xml` permitting `10.0.2.2` and `localhost` in debug.
- Make the base URL injectable:
  ```dart
  static const String _host = String.fromEnvironment('API_HOST',
      defaultValue: '10.0.2.2');
  static const String nlpBaseUrl = 'http://$_host:8002';
  ```
  Document `flutter run --dart-define=API_HOST=192.168.1.5`.
- iOS: add an `NSAppTransportSecurity` exception for local development only.

### F3. Call QA for real
**File:** `voicefront_backend_service.dart`
```dart
static const qaBaseUrl = 'http://$_host:8004';

static Future<Map<String, dynamic>> runQa(String html) async {
  final res = await http
      .post(Uri.parse('$qaBaseUrl/v1/qa/run'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'html': html}))
      .timeout(const Duration(seconds: 90));
  if (res.statusCode != 200) throw QaException(res.statusCode);
  return jsonDecode(res.body)['qa_report'] as Map<String, dynamic>;
}
```
- In `chat_screen.dart`, after layout, call `runQa(html)`, store `qaViolations = report['total_violations']`, and pass the report to the preview.
- Replace `PreviewQAScreen`'s literals with values from the report. Delete `99.2%`, `1.2s`, `0 Critical`, `2 Warnings`.
- If QA is down, show "QA unavailable" — never a green pass.

### F4. Make edits re-render
**File:** `chat_screen.dart:122-141`
```dart
Future<void> _dispatchIntent(String op, String value) async {
  final updated = Map<String, dynamic>.from(_currentSpec!);
  switch (op) {
    case 'set_hours': updated['hours'] = [value]; break;
    case 'set_theme': updated['description'] = '${updated['description'] ?? ''} · $value'; break;
    case 'add_banner': updated['description'] = '$value ${updated['description'] ?? ''}'.trim(); break;
  }
  final layout = await VoiceFrontBackendService.generateLayout(updated, updated['category']);
  final qa = await VoiceFrontBackendService.runQa(layout['html']);
  setState(() {
    _currentSpec = updated;
    _messages.add(ChatMessage(text: 'Updated ✓', type: MessageType.result,
        htmlPreview: layout['html'], storefrontSpec: updated,
        qaViolations: qa['total_violations']));
  });
}
```
- Either implement `theme` properly in the backend (palette override) or remove the chip. Do not report success for a no-op.

### F5. Real publish
- Add `publishBaseUrl` and `publish()` calling `/v1/publish`; wire all three Publish buttons.
- Show the returned `live_url` and make it tappable via `url_launcher`.
- If publish-service is unavailable, disable the button with a tooltip.

### F6. Fix the chat loop bugs
- Add `if (!mounted) return;` before every `setState` after an `await`.
- Retry must replay **the last user message**, not the first:
  ```dart
  final last = _messages.lastWhere((m) => m.isUser, orElse: () => _messages.first);
  ```
- Remove artificial `Future.delayed` waits; drive the stage indicator from actual call start/end.
- Add timeouts to every HTTP call (30 s NLP, 30 s layout, 90 s QA).
- `stopGeneration` should cancel in-flight work (`CancelableOperation` or an operation token checked after each await).

### F7. Escape the client-side fallback HTML
**File:** `voicefront_backend_service.dart:116`
```dart
import 'dart:convert';
String esc(Object? v) => const HtmlEscape(HtmlEscapeMode.element).convert('$v');
```
Apply to every interpolated field, or delete the local HTML fallback and show an error card instead. Deleting is safer and simpler.

### F8. Navigation and dead code — pick one
- **Option A (fastest):** delete `home_screen.dart`, `record_screen.dart`, `review_edit_screen.dart`, `preview_qa_screen.dart`, `storefronts_screen.dart`, `bottom_nav_bar.dart`, `category_card.dart`, `recent_storefront_card.dart`, `pill_button.dart`, `status_badge.dart`, `spacing.dart`, and `groq_api_service.dart`.
- **Option B:** wire Home → Record → Review → Preview → QA from `main.dart` and keep the flow.
Choose A if the chat is the demo. Either way, no unreachable screen remains.

### F9. Theme and dark mode
- Remove the fixed `Brightness.dark` status-bar call; use `AnnotatedRegion<SystemUiOverlayStyle>` inside `MainShell` driven by `Theme.of(context).brightness`.
- Replace remaining `AppColors.white`-as-surface with `colorScheme.surface`.
- Move repeated widget styling into `cardTheme`, `inputDecorationTheme`, `filledButtonTheme`.
- Bundle Inter locally (`google_fonts` can fall back offline) or accept the flash and document it.

### F10. Accessibility
- Add `Semantics(label: ...)` or `Tooltip` to every icon-only control.
- Give the mic and send buttons labels.
- Verify 2× text scale: replace fixed `childAspectRatio` grids with `IntrinsicHeight` lists or scrollable cards.
- Add `MediaQuery.disableAnimations` guard around the pulse animation.
- Add `onTapLink` to `MarkdownBody` and open via `url_launcher`.

### F11. Real voice (optional but required for "P1 A+")
- Add `record` + `permission_handler`.
- Capture 16 kHz mono, upload to `/v1/asr/transcribe`, and put the transcript in the input field.
- Keep the simulated path behind a debug flag.

### F12. `apps/web`
Either delete the four empty pages and the 0-byte Dockerfile, or implement them with the existing `api-client`. A 0-byte file is a claim; an absent file is not.

---

## 10. Phase T — Tests, evaluation, CI

| Step | Deliverable | Gate |
|---|---|---|
| **T1** | Non-empty `test_wcag_compliance.py`: generate 5 categories, run QA, assert zero critical | Runs in the QA container |
| **T2** | `test_ttl_stopwatch.py`: wall-clock prompt → QA report; write JSON results | Produces a number for Chapter 4 |
| **T3** | `test_lighthouse_ci.py`: Lighthouse CI against a locally served generated page | thresholds as warnings until measured |
| **T4** | `test_repair_latency.py`: deterministic vs LLM latency | median < 800 ms for deterministic |
| **T5** | Contract tests per endpoint against `api_contracts.md` | 400/404/409/422 paths covered |
| **T6** | Golden prompt set S1–S6 with assertions and a Markdown results table | committed table regenerated by CI |
| **T7** | `pytest.ini` gains `testpaths = tests services/*/tests` | a root `pytest` collects only project tests |
| **T8** | Coverage gates: 80 % on `core/` for nlp/layout/qa | CI fails below |

---

## 11. Phase D — Documentation and claims

| Step | Action |
|---|---|
| **D1** | Write `README.md`: what it is, architecture diagram, quickstart, env vars, demo script, known limitations. |
| **D2** | Write `CLAUDE.md` for future sessions. |
| **D3** | Add `.gitattributes` (`* text=auto eol=lf`) and renormalise; `git checkout --` the ~45 platform files with zero semantic change. |
| **D4** | Rewrite `docs/UPDATES.md` to describe only shipped features; delete the template-switching claim. |
| **D5** | Update `IMPLEMENTATION_COMPLETE.md` and `MASTER_PLAN_V2_FINAL.md` to match measured reality, or mark them superseded. |
| **D6** | Regenerate the deck per `DECK_CHANGES_v2.md`; one rule count (18), repair status accurate, metrics labelled measured/target. |
| **D7** | Fill Chapter 4 tables from T6/T2/T4 output. No target quoted as a result. |

---

## 12. Defect → step traceability (nothing left behind)

| Audit finding | Closed by |
|---|---|
| Autoescape off for `.jinja2` | S1 |
| JSON-LD `<script>` breakout | S1, S2 |
| Invalid template JSON-LD commas | S2 |
| `version_id` traversal (QA, publish, S3 key) | S3 |
| `/scrape` SSRF | S4 |
| Browser fingerprint in published pages | S5 |
| Hardcoded WhatsApp number / missing assets / Unsplash | S6 |
| `_PAGE_SHELL` `.format` crash | S7 |
| `price=None` crash; `location.raw_text`; currency | S8 |
| Empty `LAYOUT_TEMPLATE_DIR` | S9 |
| Groq keys on disk; env-name drift; JWT fallback secret; tracked `.env.local`; `opencode.json` | G1, S10 |
| No auth / rate limits / body caps | S11 |
| Root containers; no `.dockerignore`; curl healthchecks | S12 |
| Component library dead code; tautological test | L2, L3 |
| `lang="hi"`; missing meta/landmarks | L4 |
| Missing `httpx` | Q1 |
| Errors mapped to 500 | Q2 |
| Whole-page repair; last-patch-wins; `was_repaired` always true | Q3, Q4 |
| `auto_repair` result never returned/persisted | Q4 |
| `passed` semantics | Q5 |
| Inert focus check | Q6 |
| SORT/LEARN stubs | Q7, Q8 |
| ASR fabricated 200; no size cap; retry-everything; blocking call | A1–A4 |
| No WER; language echo | A5, A6 |
| `GROQ_MODEL` ignored; `food` default; tagline bug; unbounded prompt; `invalid_fields` drift | N1–N4 |
| No schema F1 | N5 |
| Publish QA gate always True; URL/key mismatch; fake prefix test; no CORS; 0-byte Dockerfile; absent from compose | P1–P5 |
| Healthchecks; resource limits; missing depends_on | I1, S12 |
| Terraform public bucket, no CloudFront; empty `.tf` | I2, I3 |
| No CI | I4 |
| Flutter untracked; test doesn't compile; lock drift | F1 |
| Release can't reach backend | F2 |
| QA never called; fabricated metrics | F3 |
| Edits don't re-render; silent no-ops | F4 |
| Publish no-op | F5 |
| `setState` after dispose; retry replays first prompt; no timeouts | F6 |
| Client fallback XSS | F7 |
| ~1,150 dead lines | F8 |
| Dark mode; semantics; text scaling | F9, F10 |
| Simulated voice | F11 |
| Empty `apps/web` | F12 |
| Empty E2E files; fake eval; `testpaths` | T1–T8 |
| Docs contradictions; empty README; no `CLAUDE.md`; CRLF churn | D1–D7 |
| `scrapy/` nested repo; `docs.zip`; binaries | S12, D3 |

---

## 13. Execution order, effort, and PR sequence

| PR | Contents | Effort | Blocks |
|---|---|---|---|
| **PR-0** | G1–G5 (keys, branch, backup, `.gitattributes`, commit) | 2 h | everything |
| **PR-1** | S1–S9 (renderer security + correctness) | 1.5 d | PR-2 |
| **PR-2** | S10–S12 (secrets, auth, containers) | 1 d | deploy |
| **PR-3** | Q1–Q8 (QA repair, codes, SORT/LEARN) | 2 d | publish gate |
| **PR-4** | A1–A6, N1–N5 (ASR/NLP correctness) | 1.5 d | eval |
| **PR-5** | P1–P5 + I1–I3 (publish + infra) | 1.5 d | live URL |
| **PR-6** | I4 + T1–T8 (CI + evaluation) | 1.5 d | evidence |
| **PR-7** | F1–F12 (Flutter) | 2.5 d | demo |
| **PR-8** | L2–L3 (component library real) | 1 d | visual claims |
| **PR-9** | D1–D7 (docs, deck, report) | 1 d | submission |

**Critical path:** PR-0 → PR-1 → PR-3 → PR-5 → PR-7 → PR-9. Roughly **9–11 focused working days** for one person, or **4–5 days** for a four-person team splitting services.

---

## 14. A+ acceptance checklist

Copy this into the PR description. Every box needs a link to a green run.

**Security**
- [ ] No `gsk_`, `sk-`, `AKIA`, or JWT fallback in the tree or history
- [ ] Adversarial `shop_name`/`description` cannot inject HTML or break JSON-LD
- [ ] `../`, absolute paths, and URL-encoded traversal rejected with 400
- [ ] `/scrape` rejects private/loopback/link-local and non-80/443 targets
- [ ] Rate limits return 429; publish/scrape require an API key
- [ ] Containers run non-root; `/health` green on slim images

**ASR**
- [ ] Live mode returns 503 on upstream failure; no fabricated 200
- [ ] Uploads over 25 MB → 413; wrong magic bytes → 400
- [ ] WER measured on ≥20 clips, number recorded

**NLP**
- [ ] Fallback never invents a category
- [ ] `invalid_fields` matches the documented shape
- [ ] Field-level F1 measured on ≥30 gold prompts

**Layout**
- [ ] Five categories render five distinct templates
- [ ] `price=None` renders "Ask for price"
- [ ] Location renders from `address/city/state/pincode`
- [ ] Component variants appear in output (marker test passes)
- [ ] JSON-LD parses in every category

**QA**
- [ ] `auto_repair` reduces critical violations on `fixture-bad.html`
- [ ] Returned HTML is valid, retains shop name, and is re-detected
- [ ] 400/404/500 mapped correctly
- [ ] SORT ranking visible; LEARN store reused
- [ ] WCAG pass rate measured across 5 categories × 5 viewports

**Publish**
- [ ] Refuses to publish when QA fails (test with a deliberately bad bundle)
- [ ] Returned URL serves the uploaded object
- [ ] CloudFront + OAC declared; bucket is private
- [ ] Service builds from its Dockerfile and is in compose

**Client**
- [ ] Release manifest reaches the backend
- [ ] QA report shows real counts
- [ ] Edits re-render and re-run QA
- [ ] Publish returns a real URL
- [ ] `flutter analyze --fatal-infos` and `flutter test` pass
- [ ] No unreachable screens
- [ ] Dark mode legible; every icon-only control labelled

**Engineering**
- [ ] CI green on every service
- [ ] Every metric in `testing.md` has a runnable script
- [ ] `README.md`, `CLAUDE.md`, `.gitattributes` present
- [ ] Docs contain no claim that the code cannot demonstrate

---

## 15. Things that will still not be "A+" by inspection

Be honest about these in the report; a panel respects named limits:

1. **Multilingual voice** remains out of scope until real audio + Indic normalisation exists.
2. **FAISS/CodeBERT learning** is replaced by a simpler rule store — say "rule accumulation", not "continual learning".
3. **CloudFront custom domain** needs an ACM certificate in `us-east-1` and DNS; the default `*.cloudfront.net` URL is enough for a demo.
4. **No multi-tenancy or auth for end users**; API-key auth protects the service, not accounts.
5. **Repair cannot fix contrast or heading semantics reliably** — those stay `manual`.
6. **Load testing** is not included; claim single-tenant only.

If those six sentences appear in the report, the A+ on engineering integrity is defensible. If any of them is contradicted by a slide, the deck is the weaker document.
