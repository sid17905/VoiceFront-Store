# VoiceStorefront — Component Architecture & Logic

This expands each of the five pipeline layers (L1–L5) from the theoretical framework
into concrete component logic. Read alongside `flow.md` for how these components call each other.

---

## L1 — Speech Acquisition (`apps/web`, `apps/mobile`)
**Responsibility:** capture raw audio and hand off a clean WAV blob.

Logic:
1. Capture via WebRTC (`getUserMedia`) on web, Expo AV on mobile.
2. Client-side resample to 16kHz mono before upload (reduces payload size and server load).
3. Chunk into ≤30s segments client-side if recording exceeds Whisper's context window.
4. Upload via `POST /asr/transcribe` (multipart) or stream over WebSocket for live partials (stretch goal, not MVP).

Failure handling: if mic permission denied, fall back to file upload path. No audio is discarded silently — every failed capture attempt is logged client-side for the pilot's usability metrics (task completion rate).

---

## L2 — ASR & Normalisation (`services/asr-service`)
**Responsibility:** `WAV → clean transcript`.

**Updated hosting note:** Whisper-large-v3 runs on Groq's hosted API (see `inference_hosting_plan.md`), not as a locally-loaded model. This doesn't change the logic below — it changes where step 2 executes.

Logic:
1. `language_detect.py` runs IndicLID on the first 5s segment → language code.
2. `whisper_engine.py` calls the Groq-hosted `whisper-large-v3` endpoint, passing the detected language code as the `language` parameter (Groq's API accepts ISO-639-1 codes directly — same effect as the forced-decode-token approach, just via an API param instead of a local model call). **Verify Marathi (`mr`) behavior specifically before relying on it** — Hindi and English are confirmed well-supported through Groq; Marathi support is less documented and should be tested directly against real clips rather than assumed. This is also why the framework already lists Marathi as a stretch goal, not an MVP commitment.
3. `normalize.py` runs three passes in sequence, always in this order (order matters — transliteration before punctuation restoration corrupts casing otherwise):
   - Devanagari normalisation (Indic NLP Library)
   - Roman→Indic transliteration for code-mixed tokens (IndicXlit)
   - Punctuation restoration (fine-tuned BERT)
4. Output: `{transcript: str, language: str, confidence: float, segments: [...]}`.

Design constraint: this service must be stateless — it never persists audio. Retention of raw audio, if needed for retraining, is a separate, explicit opt-in write to S3, not a side effect of this service.

Fallback: if Groq is unreachable or rate-limited (`ASR_SELF_HOSTED_FALLBACK` in `environment.md`), the service can fall back to a local `faster-whisper` instance — normally disabled, enabled only for the Month 5 self-hosted validation run described in `deployment.md` §7.

---

## L3 — Intent Extraction & Schema Builder (`services/nlp-service`)
**Responsibility:** `transcript → validated StorefrontSpec JSON`.

**Updated hosting note:** the schema-fill LLM (Llama-3.1-8B, or Llama-3.3-70B for higher quality) runs on Groq's hosted API, not a locally-run Ollama instance (see `inference_hosting_plan.md`). Llama-3.1/3.3's officially supported languages include Hindi — genuinely reliable, not just "the model happens to output something." Marathi is **not** on that supported list at all, for any hosting method — this is a model-choice limitation from the original framework, not something Groq introduced, and it's why Marathi stays a stretch goal rather than an MVP commitment.

Logic — two-pass, matching the theoretical framework's RAG-grounded design:
1. **Pass 1 (NER):** IndicBERT token classifier (still local — small enough to run on any teammate's CPU) tags spans as one of `SHOP_NAME, PRODUCT, PRICE, CATEGORY, HOURS, LOCATION, CONTACT, DESCRIPTION`.
2. **Pass 2 (Schema fill):** `schema_builder.py` calls the Groq-hosted LLM with: raw transcript + NER spans + `StorefrontSpec` JSON Schema definition + 3 few-shot examples. It resolves ambiguity, infers missing fields, normalises formats (price → INR float, hours → ISO 8601).
3. **Validation loop:** run output against JSON Schema v7. If a field fails, re-prompt the LLM with only that field's error message appended — not the whole schema again. This targeted re-prompt is the mechanism behind the 94.7% first-pass validity figure; a full re-prompt would be slower and less precise.
4. Cap re-prompt loop at 2 retries — if still invalid, surface the failing field to the user for manual correction in the review UI rather than looping indefinitely.
5. Groq's free tier is rate-limited per-minute, not just per-day — if multiple teammates test simultaneously, expect occasional 429s. `schema_builder.py` should back off and retry (`NLP_GROQ_RATE_LIMIT_BACKOFF_SEC`), not fail the request outright.

---

## L4 — Layout Synthesiser (`services/layout-service`)
**Responsibility:** `StorefrontSpec JSON → HTML/CSS/JS bundle`.

Logic:
1. `template_classifier.py`: TF-IDF vector of the shop description → k-NN against the 5 (MVP) category templates → best-match template ID. This is a classification step, not generation — MVP scope explicitly excludes freeform layout generation.
2. `palette_engine.py`: category → colour palette lookup, grounded in Labrecque & Milne (2012) colour-psychology mappings.
3. `renderer.py`: Jinja2 server-side render, injecting: product grid (CSS Grid), hours (JSON-LD for SEO), contact block (WhatsApp deep link + Maps embed).
4. Output bundle is validated for size/structure before being handed to QA — this is a cheap pre-check, not a substitute for the QA pipeline.

Constraint: Jinja2 is logic-less by design — never let a template call back into Python logic. All conditional structure must be resolved in `renderer.py` before the template sees the context dict. This is what keeps templates safe from injection.

---

## L5 — Self-Healing QA + Publisher (`services/qa-service`, `services/publish-service`)
**Responsibility:** `HTML bundle → live URL + QA report`, self-improving over time.

Four-phase logic, always run in this order:
1. **SORT:** failure-probability model ranks sections (product grids, navbars, map embeds historically fail most) so DETECT spends its budget where violations are likely — this is what delivers the 38% compute reduction.
2. **DETECT:** Playwright renders the bundle at 5 viewport widths; a constraint graph checks 400+ rules (WCAG 2.2 AA + structural + rendering fidelity).
3. **REPAIR:** each violation is embedded and matched against the FAISS repair-pattern store (cosine similarity > 0.87). A match → apply the stored patch. No match → LLM-assisted repair (Groq-hosted Llama, same as `nlp-service` — see `inference_hosting_plan.md`) generates a new patch. Target: <800ms per violation (note: this target assumed local inference originally; a Groq API round-trip adds network latency, so validate this target still holds once Groq is the actual path — see `testing.md`).
4. **LEARN:** every *successfully applied* repair (verified by re-running DETECT on the patched section) is embedded via CodeBERT and written into the FAISS index — this is the continual-learning loop. Failed repairs are never written back; only confirmed fixes.

Publish: once QA passes threshold (0/critical violations, ≤ MVP-defined minor-violation budget), `publish-service` uploads the bundle to S3 and invalidates/warms the CloudFront distribution, then returns the live URL.

---

## Cross-cutting: what "self-healing" does *not* mean here
Worth being explicit for your viva: the system does not retrain the LLM or the NER model from production data in the MVP (that's explicitly out-of-scope, deferred to v2.0). "Learning" in the MVP is scoped narrowly to the FAISS repair-rule store — it's rule accumulation, not model fine-tuning. Don't overstate this in your defense; a panel member who knows continual learning literature will ask, and "we accumulate verified repair patches in a vector store, we don't fine-tune" is the accurate, defensible answer.
