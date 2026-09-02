# VoiceStorefront — Environment Variables

Naming convention (per `common_references.md`): `{SERVICE}_{RESOURCE}`. Every service reads
its own prefix only — a service should never read another service's env var directly; if it
needs a value another service owns, that value comes over the wire in the API response, not
through shared environment leakage.

Each service ships an `.env.example` mirroring its section below. Real `.env` files are
git-ignored; secrets in prod come from AWS Secrets Manager, not plain env files.

---

## Global (read by every service via `packages/common-utils/config.py`)
| Variable | Purpose | Dev value | Prod source |
|---|---|---|---|
| `ENV` | `development \| staging \| production` | `development` | CI/CD sets per environment |
| `LOG_LEVEL` | `DEBUG \| INFO \| WARNING \| ERROR` | `DEBUG` | `INFO` |
| `DATABASE_URL` | Postgres connection string | local docker-compose Postgres | RDS `db.t3.micro` endpoint |
| `REDIS_URL` | Redis connection string (qa-service only, per `integration.md`) | local docker-compose Redis | Redis container on the same `t3.micro` — no ElastiCache |
| `GROQ_API_KEY` | Shared inference credential — Whisper + Llama-3, per `inference_hosting_plan.md` | personal free-tier key per teammate during dev | one team-owned key for staging/pilot |

## asr-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `ASR_GROQ_MODEL` | Which Groq-hosted Whisper model to call | `whisper-large-v3` | `whisper-large-v3` (or `whisper-large-v3-turbo` if speed matters more than the last bit of accuracy) |
| `ASR_MAX_AUDIO_DURATION_SEC` | Reject uploads longer than this | `300` | `300` |
| `ASR_ALLOWED_FORMATS` | Comma-separated | `wav,mp3,ogg` | same |
| `ASR_SELF_HOSTED_FALLBACK` | `true \| false` — whether to fall back to local `faster-whisper` if Groq is unreachable/rate-limited | `false` (not installed locally by default) | `false` in normal operation; `true` only during the Month 5 self-hosted validation run (`deployment.md` §7) |

## nlp-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `NLP_NER_MODEL_PATH` | Fine-tuned IndicBERT weights (still local — small, CPU-friendly, not a Groq-hosted model) | local dir | S3-backed artifact |
| `NLP_GROQ_MODEL` | Which Groq-hosted LLM to call for schema-fill | `llama-3.1-8b-instant` | `llama-3.3-70b-versatile` if quality needs outweigh the tighter free-tier limits on the bigger model |
| `NLP_SCHEMA_RETRY_LIMIT` | Max re-prompt loops (see `Architect.md`) | `2` | `2` |
| `NLP_GROQ_RATE_LIMIT_BACKOFF_SEC` | Wait-and-retry delay when Groq's per-minute limit is hit | `5` | `5` — see `testing.md` note on batching benchmark runs |

## layout-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `LAYOUT_TEMPLATE_DIR` | Path to Jinja2 templates | `./data/templates` | baked into container image |
| `LAYOUT_CATEGORIES` | Comma-separated MVP categories | `food,apparel,electronics,pharmacy,services` | same |

## qa-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `QA_FAISS_INDEX_PATH` | Path to persisted FAISS index | local file | persisted on the `t3.micro`'s attached EBS volume (survives restarts) |
| `QA_SIMILARITY_THRESHOLD` | Cosine similarity cutoff for repair match | `0.87` | `0.87` — do not tune casually, it's cited in the report |
| `QA_GROQ_MODEL` | LLM used for the repair-engine's LLM-assisted fallback (per `Architect.md` L5) | `llama-3.1-8b-instant` | same |
| `QA_MAX_REPAIR_LATENCY_MS` | Alert threshold, not a hard limit | `800` | `800` |
| `QA_VIEWPORT_WIDTHS` | Comma-separated | `320,375,768,1024,1440` | same |

## publish-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `PUBLISH_S3_BUCKET` | Target bucket for storefront bundles | `voicestorefront-dev` | `voicestorefront-prod` |
| `PUBLISH_CLOUDFRONT_DIST_ID` | For invalidation calls | dev distribution | prod distribution |
| `PUBLISH_AWS_REGION` | — | `ap-south-1` | `ap-south-1` |

## apps/web
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL the frontend proxies to | `http://localhost:8000` | internal gateway URL |
| `NEXT_PUBLIC_MAPS_EMBED_KEY` | Google Maps embed key (client-safe, restricted by domain) | dev key | prod key, domain-restricted |

## Secrets that must NEVER go in a plain `.env` even in dev
`GROQ_API_KEY`, `Google Places API key` (server-side lookups in `schema_builder.py`), AWS access
keys — use local AWS profile / instance role instead. If any of these show up hardcoded in a
commit, treat it as a blocking issue before the mentor demo, not a cleanup task for later. For
the shared staging/pilot `GROQ_API_KEY` specifically: one team member owns it, it lives in AWS
Secrets Manager (or at minimum a non-committed `.env` on the staging box only), and it gets
rotated if it's ever pasted into a chat, a shared doc, or a public repo by mistake.
