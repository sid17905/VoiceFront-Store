# VoiceFront-Store

A prompt-to-storefront pipeline: an English retail prompt is validated against a
shared Pydantic schema, rendered into a mobile-first storefront page, checked by a
real Playwright + axe-core accessibility audit, and published to a private S3 bucket
behind CloudFront.

## Architecture

Five independently deployable services:

| Service | Port | Responsibility |
|---|---|---|
| `asr-service` | 8001 | Audio transcription via Groq Whisper (`/v1/asr/transcribe`) |
| `nlp-service` | 8002 | Prompt → `StorefrontSpec` extraction (`/v1/nlp/extract`) |
| `layout-service` | 8003 | Spec → HTML storefront (`/v1/layout/generate`) |
| `qa-service` | 8004 | Browser-based accessibility audit + repair (`/v1/qa/run`) |
| `publish-service` | 8005 | Bundle validation, S3 upload, CloudFront invalidation (`/v1/publish`) |

All services share `packages/common_utils` (Groq client, service app factory,
security middleware, exceptions) and `packages/schemas` (Pydantic single source of
truth; JSON Schema and TypeScript are generated, never hand-edited).

## Quickstart

```bash
# 1. Install shared packages (editable, no sys.path hacks)
pip install -e packages

# 2. Install service dependencies and run
pip install -r services/nlp-service/requirements.txt
python -m uvicorn services.nlp-service.main:app --port 8002
```

Set `GROQ_API_KEY` in `.env` (kept out of git). Without it every service falls back
to deterministic heuristics and reports `"mode": "fallback"` in `/health`.

## Known limitations

- **Multilingual voice** is out of scope; `language_detect` is a stub and Whisper's
  detected language is not yet used.
- **Repair learning** is a deterministic rule store, not FAISS/continual learning.
- **CloudFront custom domain** requires an ACM certificate in `us-east-1`; the
  default `*.cloudfront.net` URL is sufficient for a demo.
- **No end-user auth or multi-tenancy**; API-key auth protects the service, not
  accounts.
- **Repair cannot fix contrast or heading semantics** reliably; those remain
  `manual` in the QA report.
- **Load testing** is not included; the system is single-tenant.