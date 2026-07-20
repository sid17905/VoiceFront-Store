# VoiceStorefront — Security

Scoped deliberately to the MVP's real attack surface, not a generic checklist — a single-tenant,
no-login academic project has a small but real set of things worth getting right.

## 1. File upload validation (asr-service)
The audio upload endpoint (`POST /v1/asr/transcribe`) is the only endpoint that accepts arbitrary
binary input from a browser, which makes it the highest-risk surface in the system.
- Enforce `ASR_ALLOWED_FORMATS` and `ASR_MAX_AUDIO_DURATION_SEC` (see `environment.md`) server-side,
  not just client-side — a client-side-only check is not a control, it's a UX nicety.
- Validate actual file content (magic bytes), not just the extension or declared MIME type.
- Reject before decoding into the full pipeline if size/duration checks fail — don't let a
  malformed or oversized file reach `whisper_engine.py` and consume GPU/CPU time.

## 2. Injection surfaces
- **Jinja2 templates (layout-service):** templates are logic-less by convention (see `Architect.md`)
  — this is a security control, not just a style preference. All values from `StorefrontSpec` are
  auto-escaped by Jinja2's default autoescaping; never disable it, and never construct raw HTML
  strings from user-spoken content and inject with `|safe`.
- **SQL:** all Postgres access through an ORM/parameterized queries — no string-formatted SQL,
  anywhere, including "just this one debug query."
- **LLM prompt injection (nlp-service):** the transcript is user-controlled input fed into an LLM
  prompt. Treat it as untrusted — the LLM's output is validated against the `StorefrontSpec` JSON
  Schema (already required functionally per `Architect.md`), which incidentally also bounds the
  blast radius of a prompt-injection attempt: the worst case is a malformed/unexpected field value,
  not arbitrary code execution, because the schema validator constrains what can flow downstream.

## 3. S3 / CloudFront (publish-service)
- Bucket policy: public read only on the specific prefix serving published storefronts; everything
  else (raw audio if retained, intermediate bundles) stays private, accessed only via signed
  service-role credentials.
- No public write access under any circumstance — only `publish-service`'s IAM role can write.
- CloudFront: HTTPS-only (redirect HTTP → HTTPS), no permissive CORS beyond what the published
  storefronts themselves need.

## 4. Rate limiting
No auth layer in MVP (per `integration.md` §6) means rate limiting is your main abuse control:
- Per-IP rate limit on `POST /v1/asr/transcribe` (the most expensive endpoint) — even a simple
  fixed-window limiter at the ALB/API-gateway layer is enough for a pilot; don't over-engineer this.
- Same for `POST /v1/qa/run` given LLM-assisted repair cost.

## 5. Secrets management
- No AWS keys or API keys in `.env` files committed to git — see the explicit list in `environment.md`.
- Google Places API key: server-side only, never exposed to the browser (distinct from the
  `NEXT_PUBLIC_MAPS_EMBED_KEY`, which is intentionally client-safe and domain-restricted).
- Rotate any key that touches a public demo or pilot before and after the event.

## 6. Data handling
- Raw audio: not retained by default (per `Architect.md` — asr-service is stateless). If you do
  retain audio for retraining, that's an explicit opt-in write to S3 with its own bucket policy,
  and pilot users need to be told their voice is stored — don't let this become a silent side effect.
- No PII beyond what a shop owner voluntarily states (shop name, location, contact number) — treat
  the phone number/WhatsApp contact field as the only quasi-sensitive field in the system, and
  don't log it in plaintext application logs.

## 7. What's explicitly out of scope (name this to your mentors, don't let it surface as a surprise)
- No penetration testing.
- No formal threat model beyond this document.
- No auth/authorization system — anyone with the app URL can use it during the pilot. Acceptable
  for a controlled 50-user pilot cohort; would not be acceptable if this went further.
