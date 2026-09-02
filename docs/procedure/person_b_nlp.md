# Person B — Understanding / Schema-Building (nlp-service)

Owns: `services/nlp-service/` — everything between a transcript in and a validated
`StorefrontSpec` JSON out. Read `Architect.md` (L3 section) and `data.md` for the "why."

---

## Phase 0 — Setup

- [ ] Pull the repo once scaffolded; confirm Docker Compose runs on your machine.
- [ ] Copy `services/nlp-service/.env.example` to `.env`, fill in local values per `environment.md` (`NLP_GROQ_MODEL`, `NLP_SCHEMA_RETRY_LIMIT`).
- [ ] Get a free Groq API key, set `GROQ_API_KEY` in your `.env` — no need to install Ollama, Llama-3 runs on Groq's hosted API now (see `inference_hosting_plan.md`).
- [ ] Confirm you can hit your own stub service's root endpoint once it's in the compose file.
- [ ] Sign off in writing that you own `nlp-service`.

## Phase 1 — Foundation

**Shared, do this with the team first:**
- [ ] Co-lead the `StorefrontSpec v1.0` schema draft (`packages/schemas/storefront_spec.schema.json`) — you're the one building against it most directly, so push hard on getting the field list and types right before it's frozen.
- [ ] Help write `packages/schemas/entity_types.py` / `entity_types.ts` — the 8 entity types (`SHOP_NAME, PRODUCT, PRICE, CATEGORY, HOURS, LOCATION, CONTACT, DESCRIPTION`) your NER model will tag.

**Your own work:**
- [ ] Set up IndicBERT base model locally; confirm inference runs on a sample sentence (this one stays local — it's small and CPU-friendly, unlike the LLM).
- [ ] Draft the NER fine-tuning dataset plan — what entity-tagged sentences you'll need, and how many.
- [ ] Write `services/nlp-service/core/ner_model.py` — initially against the un-fine-tuned base model (swap in the fine-tuned version in Phase 3).
- [ ] Draft 3 few-shot examples in `services/nlp-service/prompts/` for the LLM schema-fill step; test them directly against Groq's `llama-3.1-8b-instant` endpoint — Hindi is officially supported by Llama-3.1, so this should work well; Marathi is not on the officially supported list for this model, for any hosting method, so don't be surprised if it's weaker.
- [ ] Write `services/nlp-service/core/schema_builder.py` — calls Groq (via the shared `packages/common-utils/groq_client.py`) with transcript + NER spans + schema definition + few-shot examples.
- [ ] Write `services/nlp-service/core/schema_validator.py` — JSON Schema v7 validation, with the 2-retry re-prompt loop (append only the failing field's error, not the whole schema, on retry).
- [ ] Write `services/nlp-service/routers/extract.py` wiring: ner_model → schema_builder → schema_validator, matching `api_contracts.md` (`POST /v1/nlp/extract`), including the `is_valid: false` + `invalid_fields` response shape for exhausted retries.
- [ ] Add retry/backoff handling for Groq's per-minute rate limit (`NLP_GROQ_RATE_LIMIT_BACKOFF_SEC`) — a 429 from Groq should trigger a short wait-and-retry, not a hard failure.

## End of Phase 1 checkpoint
- [ ] Your service turns at least one real transcript into a structurally valid `StorefrontSpec`.
- [ ] Confirm with Person A that you're correctly consuming their `{transcript, language}` output.
- [ ] Confirm with Person C that the `StorefrontSpec` shape you're producing is exactly what `layout-service` expects as input.
