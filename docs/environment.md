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
| `DATABASE_URL` | Postgres connection string | local docker-compose Postgres | RDS endpoint, Secrets Manager |
| `REDIS_URL` | Redis connection string (qa-service only, per `integration.md`) | local docker-compose Redis | ElastiCache endpoint |

## asr-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `ASR_WHISPER_MODEL_PATH` | Path/name of Whisper-large-v3 weights | local cached model dir | S3-backed model artifact, pulled at container start |
| `ASR_MAX_AUDIO_DURATION_SEC` | Reject uploads longer than this | `300` | `300` |
| `ASR_ALLOWED_FORMATS` | Comma-separated | `wav,mp3,ogg` | same |

## nlp-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `NLP_NER_MODEL_PATH` | Fine-tuned IndicBERT weights | local dir | S3-backed artifact |
| `NLP_LLM_ENDPOINT` | Ollama server URL | `http://localhost:11434` | internal VPC endpoint |
| `NLP_LLM_MODEL_NAME` | `llama-3-8b \| gemma-2-9b` | `llama-3-8b` | same, pinned per release |
| `NLP_SCHEMA_RETRY_LIMIT` | Max re-prompt loops (see `Architect.md`) | `2` | `2` |

## layout-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `LAYOUT_TEMPLATE_DIR` | Path to Jinja2 templates | `./data/templates` | baked into container image |
| `LAYOUT_CATEGORIES` | Comma-separated MVP categories | `food,apparel,electronics,pharmacy,services` | same |

## qa-service
| Variable | Purpose | Dev value | Prod |
|---|---|---|---|
| `QA_FAISS_INDEX_PATH` | Path to persisted FAISS index | local file | EFS-mounted volume (survives container restarts) |
| `QA_SIMILARITY_THRESHOLD` | Cosine similarity cutoff for repair match | `0.87` | `0.87` — do not tune casually, it's cited in the report |
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
`Google Places API key` (server-side lookups in `schema_builder.py`), AWS access keys — use
local AWS profile / instance role instead. If any of these show up hardcoded in a commit, treat
it as a blocking issue before the mentor demo, not a cleanup task for later.
