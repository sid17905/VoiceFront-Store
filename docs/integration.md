# VoiceStorefront — Integration Logic

Covers how the independently-deployable services actually talk to each other and to
external systems, and the contracts that make that safe.

## 1. Internal service-to-service integration

All internal calls are synchronous REST over HTTP (FastAPI), not a message queue — MVP scope
doesn't need async job orchestration since the whole pipeline is bounded at 5 minutes end-to-end.

- **Transport:** JSON over HTTP, internal service mesh on a private VPC subnet (not internet-facing).
- **Contract source of truth:** every request/response body is a Pydantic model generated from
  `packages/schemas/*.schema.json` — a service never hand-writes a response shape that diverges
  from the shared schema.
- **Timeouts:** each downstream call has an explicit timeout tied to its evaluation-framework target
  (e.g. layout-service caller sets a timeout comfortably above the render budget, qa-service caller's
  timeout accounts for the ≤800ms/violation repair target × expected violation count).
- **Retries:** idempotent GETs retry with exponential backoff (via `common-utils`); POSTs that mutate
  state (schema build, publish) do **not** auto-retry — a failed mutation surfaces to the frontend for
  explicit user retry, to avoid double-publishing a storefront.

## 2. Frontend ↔ backend integration

`apps/web` never calls services directly from the browser — it goes through Next.js route handlers
in `apps/web/app/api/`, which proxy to the internal services. This keeps service URLs, internal auth
tokens, and timeouts out of client-side code.

`packages/api-client` is the single generated client apps/web imports — generated from the same
JSON Schemas as the backend Pydantic models, so a field rename in `packages/schemas` breaks the
build immediately instead of failing silently at runtime.

## 3. External API integrations

| External service | Used by | Purpose | Failure mode handling |
|---|---|---|---|
| OpenStreetMap / Google Places API | nlp-service (`schema_builder.py`) | Validate/resolve LOCATION entity, get lat/lng for Maps embed | On API failure, fall back to storing the raw spoken address text with `location_verified: false` — never block schema build on a third-party outage |
| WhatsApp Business (deep link, not an API call) | layout-service (`renderer.py`) | `wa.me/` link construction from CONTACT entity | Client-side validation only (phone format); no external call needed |
| Ollama (self-hosted Llama-3/Gemma-2) | nlp-service, qa-service (LLM-assisted repair) | Local inference, no per-token cost | Treated as internal, not external — but still behind the same timeout/retry discipline since it's a separate process |

## 4. Infra integration

- **AWS S3 + CloudFront:** `publish-service` is the only writer. Upload → CloudFront invalidation →
  return live URL only after invalidation is confirmed (not fire-and-forget), so the "live URL" returned
  to the user is actually serving the new content.
- **PostgreSQL:** shared by nlp-service (writes `StorefrontSpec`), layout-service (reads spec, writes
  bundle metadata), qa-service (writes `QAReport`), publish-service (writes publish record). One
  connection pool config per service, not a shared connection — services should be able to scale
  independently without contention.
- **Redis:** used only by qa-service as the hot cache for the FAISS repair-rule lookup layer (per
  Table 4 in the framework) — not used as a general cache elsewhere in MVP, to avoid it becoming an
  undocumented shared dependency.

## 5. CI/CD integration points
- Each `services/*` and `apps/web` has its own Dockerfile and its own GitHub Actions workflow —
  independent build/deploy, matching the "independently scalable, replaceable, testable" architecture
  principle from the framework.
- `packages/schemas` changes trigger a build check across **every** dependent service in the same PR,
  so a schema change can't merge without the services that consume it also being updated.

## 6. Auth (MVP scope note)
The framework doesn't specify an auth layer, and it's reasonable to keep the MVP single-tenant
(one shop owner session at a time, no login system) given the 6-month/4-person constraint. If your
mentors push back on this, the honest answer is: multi-tenant auth is a scope decision to make
explicitly, not an oversight — worth a line in your limitations section if it isn't there already.
