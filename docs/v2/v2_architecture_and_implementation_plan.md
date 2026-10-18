# VoiceFront-Store V2 Architecture & Implementation Plan

## Executive Summary
Version 2 of VoiceFront-Store introduces a **Prompt-First English Baseline** for presentation and rapid execution. Voice and multilingual capabilities (ASR, IndicLID, transliteration, IndicBERT) are **not removed**, but are **modularized and deferred to post-demo phases** to ensure a reliable, demo-ready pipeline. The architecture maintains clean extension points so the complete voice stack can be plugged in later without structural rework.

## 1. Architectural Changes

### The Streamlined Pipeline (Phase 1 / Presentation Scope)
The pipeline is optimized for prompt-first text input while keeping voice interface hooks intact for Phase 2:

1. **asr-service (Deferred for Presentation / Phase 2 Roadmap)**
   - **Status**: Kept in codebase architecture as a modular plug-in; omitted from active presentation flow.
   - **Future Integration**: Direct Groq Whisper-Large-v3 / Indic speech pipeline will feed transcripts directly into the NLP layer.
2. **nlp-service (V2: Prompt-First JSON Schema Extraction)**
   - **Active Flow**: Accepts direct English text prompts (or upstream transcripts) -> Uses hardened System Prompts with JSON Schema validation via Groq Llama-3.1 -> Returns typed `StorefrontSpec`.
   - **Deferred**: IndicBERT local NER extraction retained in architecture specifications for future multilingual expansion.
3. **layout-service (No Major Changes)**
   - Directly interprets V2 English `StorefrontSpec`.
   - Continues using Jinja2 static assemblies mapping entities into HTML/CSS chunks.
4. **qa-publish-service (Consolidated)**
   - Consolidates the stubbed out `publish-service` into the `qa-service` for simpler operations.
   - Flow: Playwright multi-viewport axe-core testing -> Error detection -> Simple LLM layout patching if DOM violates rules -> Pushes bundle to AWS S3 & invalidates CloudFront.

## 2. Tiny Details & Micro-Implementations

### `packages/schemas/` 
We must define strict Pydantic schemas in `packages/schemas/storefront_spec_v2.py` as the single source of truth for the Prompt-First extraction.
- **Fields**: `shop_name` (str), `category` (Literal['food', 'apparel', 'electronics', 'pharmacy', 'services']), `description` (str), `products` (List[Dict]), `hours` (str), `location` (str), `contact` (Dict).

### `asr-service` Implementation Breakdown
- **FastAPI Setup**: Implement `main.py` and `routers/transcribe.py`.
- **Core Engine**: `core/whisper_engine.py` will send FormData with the audio file to `https://api.groq.com/openai/v1/audio/transcriptions`. Parameters: `model="whisper-large-v3"`, `response_format="json"`, `language="en"`, `prompt="The audio contains details about a localized retail store, its products, prices, and operating hours."`
- **Validation**: Implement simple size-check and audio format parsing using `python-multipart`.

### `nlp-service` Implementation Breakdown
- **FastAPI Setup**: Implement `main.py` and `routers/extract.py`.
- **Schema Builder**: `core/schema_builder.py` will construct a robust Prompt Template.
  - *System Prompt Pattern*: "You are an expert intent extraction engine. Extract metadata from the given transcript into a strictly valid JSON object adhering to this schema: {injected_schema}. Infer unspecified fields gracefully."
  - *Validation Loop*: Call Groq Llama-3 API. Attempt `json.loads(response)`. Pass to Pydantic validator. Catch `ValidationError`. If invalid, append validation error string to conversation history and retry (max 2 attempts).

### `layout-service` Adaptation
- Verify that `nlp-service` V2 schema output seamlessly binds to `core/renderer.py`. 
- No major rewrite needed, but classification thresholds should be recalibrated strictly to modern English embeddings or a direct LLM-based categorization prompt instead of TF-IDF k-NN.
- **Scraping Refactor**: Replace `Playwright` with `Scrapling` in `_playwright_worker.py` and `tools/` for drastically faster and lower-overhead DOM extraction and CSS parsing when scraping design references.

### `qa-publish-service` Implementations
- Finish the Pass-through stubs in `qa-service`.
- Connect S3 bucket uploads via `boto3`.
- Set up CloudFront invalidation tasks based on static URLs.
- Return finalized `live_url` payload to client.

## 3. Infrastructure & Deployment (English/Prompt-Base Focus)
- All V2 services share a lightweight Alpine Python base image because massive torch/transformers weight caches are dead. `Dockerfile` definitions will drop from ~4GB to ~200MB per container.
- `docker-compose.dev.yml` to define `asr-service`, `nlp-service`, `layout-service`, `qa-service`, with attached simple Redis (if cache needed).
- Provision Terraform `s3_cloudfront.tf` for hosting the static sites generated.

## 4. Work Execution Path
1. **Phase 1: Schemas & Packages** - Write the strict Pydantic definitions.
2. **Phase 2: ASR Service** - Fully code `asr-service/main.py` and `whisper_engine.py`.
3. **Phase 3: NLP Service** - Code `nlp-service` zero-shot extraction logic utilizing Groq.
4. **Phase 4: API & Client Integrations** - Bind Frontend Mock API layer to hit the local Docker swarm via `localhost:8000`.
5. **Phase 5: Deploy & Testing** - Spin up E2E tests for the new streamlined pipeline.