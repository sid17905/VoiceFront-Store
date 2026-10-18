# ARCHITECTURE REPAIRS — A1–A4

Per-defect fixes are in `REMEDIATION_PLAN_TO_A_PLUS.md`. These four are **structural**: they prevent the next
generation of defects and make the agent's job tractable.

---

## A1 — One Groq client

**Problem.** Three independent call paths, three key-read strategies:
- `services/asr-service/core/whisper_engine.py` — `groq` SDK, key read per call, client built per retry.
- `services/nlp-service/core/schema_builder.py` — `groq` SDK, key read per call.
- `services/qa-service/core/repair_engine.py` — raw `httpx.post` to `https://api.groq.com/...`, key read **at import**, ignores `GROQ_MODEL` (uses `QA_GROQ_MODEL` only in docs).

**Target file:** `packages/common_utils/groq_client.py`

```python
from __future__ import annotations
import os
from functools import lru_cache
from groq import Groq

PLACEHOLDER_KEYS = {"", "mock", "placeholder", "your_groq_api_key_here"}

class GroqNotConfigured(RuntimeError):
    pass

def api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key in PLACEHOLDER_KEYS:
        raise GroqNotConfigured("GROQ_API_KEY is not configured")
    return key

@lru_cache(maxsize=1)
def client() -> Groq:
    return Groq(api_key=api_key(), timeout=60.0)

def model(kind: str = "chat") -> str:
    if kind == "chat":
        return os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    if kind == "repair":
        return os.getenv("GROQ_REPAIR_MODEL", os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"))
    if kind == "asr":
        return os.getenv("GROQ_ASR_MODEL", "whisper-large-v3")
    raise ValueError(kind)
```

**Migration.**
1. Add `groq` to a shared `requirements-base.txt`; services inherit it.
2. ASR: replace the per-attempt `Groq(api_key=…)` with `client()`, `model("asr")`.
3. NLP: same with `model("chat")`; keep the `import groq` guard only to produce a clear error.
4. QA: replace `httpx.post` with `client().chat.completions.create(...)` and `model("repair")`; delete the import-time key read.
5. `PLACEHOLDER_KEYS` exists in one place only.

**Proof.**
```bash
grep -rn "api.groq.com" services packages --include='*.py' | grep -v test   # no hits
grep -rn "Groq(api_key" services packages --include='*.py' | grep -v common_utils  # no hits
python -c "from common_utils.groq_client import model; print(model('repair'))"
```

**Risk.** Importing `common_utils` requires the package on `sys.path`. Do A4 first if the agent hits import errors; otherwise keep the existing bootstrap for one PR and remove it in A4.

---

## A2 — One service app factory

**Problem.** CORS, request-ID middleware, the global exception handler and the JSON log format are copy-pasted into five `main.py` files. They have already drifted (publish has no CORS; the log formatter declares `%(request_id)s` with no filter and raises on any record that lacks it).

**Target file:** `packages/common_utils/service_app.py`

```python
from __future__ import annotations
import logging, os, time, uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .exceptions import VoiceStorefrontError

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True

LOG_FORMAT = '{"time":"%(asctime)s","level":"%(levelname)s","service":"%(service)s","request_id":"%(request_id)s","message":"%(message)s"}'

def create_app(name: str, version: str, *, cors: bool = True) -> FastAPI:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(RequestIdFilter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    class ServiceFilter(logging.Filter):
        def filter(self, record): record.service = name; return True
    handler.addFilter(ServiceFilter())

    app = FastAPI(title=name, version=version,
                  docs_url="/docs" if os.getenv("ENV", "dev") != "production" else None,
                  redoc_url=None)

    if cors:
        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
        app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in origins],
                           allow_credentials=False, allow_methods=["GET", "POST"],
                           allow_headers=["Content-Type", "Authorization", "X-Request-ID", "X-API-Key"])

    @app.middleware("http")
    async def request_context(request: Request, call_next: Callable) -> Response:
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start = time.monotonic()
        response = await call_next(request)
        logging.getLogger(name).info(
            f"method={request.method} path={request.url.path} status={response.status_code} "
            f"ms={round((time.monotonic()-start)*1000,1)}", extra={"request_id": rid})
        response.headers["X-Request-ID"] = rid
        return response

    @app.exception_handler(VoiceStorefrontError)
    async def known_error(request: Request, exc: VoiceStorefrontError):
        return JSONResponse(status_code=getattr(exc, "status_code", 500), content=exc.to_dict())

    @app.exception_handler(Exception)
    async def unknown_error(request: Request, exc: Exception):
        logging.getLogger(name).error("unhandled: %s", type(exc).__name__)
        return JSONResponse(status_code=500, content={"error_code": "INTERNAL_ERROR",
                                                      "message": "An unexpected error occurred."})

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": name, "version": version}
    return app
```

**Migration.** Each `main.py` becomes:
```python
app = create_app("qa-service", "2.0.0")
app.include_router(qa_router)
```
The service keeps only its own extra health fields via a second route or an override hook.

**Proof.** Start all five; assert `{"status":"ok","service":<name>,"version":...}` and that a log line with no `extra` does not raise.

---

## A3 — Schemas generated, not hand-maintained

**Problem.** `entity_types.py`, `storefront_spec.schema.json`, `entity_types.ts` and `api-client/index.ts` are edited by hand and have drifted (`price` optional in Python; TS `QaViolation` fields differ from Python).

**Target:** keep Pydantic as the only authored source. Generate the rest.

`scripts/gen_schemas.py`:
```python
import json, pathlib
from packages.schemas.entity_types import StorefrontSpec, NlpExtractResponse
out = pathlib.Path("packages/schemas")
(out / "storefront_spec.schema.json").write_text(
    json.dumps(StorefrontSpec.model_json_schema(), indent=2) + "\n")
```
For TypeScript, use `datamodel-code-generator --output-model-type pydantic_v2.BaseModel` **or**
`pydantic2ts` if available; otherwise emit a small hand-written `.d.ts` from the JSON Schema and mark it generated.

**CI gate:**
```yaml
- run: python scripts/gen_schemas.py
- run: git diff --exit-code packages/schemas
```
**Proof:** regenerating produces no diff; a deliberate field rename produces a diff.

---

## A4 — Editable packages, no `sys.path` hacks

**Problem.** Every service and module inserts parents into `sys.path`. Five packages named `core` collide; `conftest` already deletes `sys.modules["core"]` to work around it.

**Target layout:**
```
packages/
  pyproject.toml            # name = "voicefront-common", packages: common_utils, schemas
services/
  nlp-service/pyproject.toml   # name = "voicefront-nlp", dependencies = ["voicefront-common"]
```
Each service package contains `core/` **inside** the package namespace, or keeps `core/` as a top-level module with `py-modules`. Recommended: rename to `voicefront_nlp` and import `voicefront_nlp.core.schema_builder`.

If a full rename is too invasive for this cycle, do the minimum that removes collisions:
1. `pip install -e packages` in every dev/CI env.
2. Delete every `sys.path.insert` block.
3. Delete the first four lines of each `conftest.py` that exist only for path bootstrapping.

**Proof.** `python -c "import common_utils, schemas"` works from the repo root without `PYTHONPATH`; `pytest` from root imports all five services' tests without `sys.modules` purges.

---

## Ordering and effort

| Step | Effort | Depends on | Payoff |
|---|---|---|---|
| A1 | 3–4 h | S10 | One place to change model/key; fixes QA ignoring `GROQ_MODEL` |
| A2 | 3–4 h | S10 | Fixes the logging crash and publish's missing CORS in one edit |
| A3 | 2–3 h | A1 | Ends schema drift permanently |
| A4 | 4–6 h | A2 | Removes the class of import bugs that make proofs unreliable |

Do **A2 before A1** if the logging crash is blocking test runs; otherwise A1 first.
