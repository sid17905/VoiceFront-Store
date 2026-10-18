# VoiceFront-Store V2: Real Setup & Production-Grade Execution Plan

## No Dummies, No Mocks: Real Setup Principles
To ensure VoiceFront-Store V2 operates on a **real, production-grade setup** without relying on static mock data or fake simulation flags during live execution:

1. **Real LLM & Transcription Inference**:
   - `GROQ_API_KEY` must be active and valid. The ASR and NLP services will enforce live calls to Groq Whisper (`whisper-large-v3`) and Llama-3 (`llama-3.3-70b-versatile`) without silent fallback overrides unless explicitly debugging offline.
2. **Real Component Harvesting (Scrapling + REA)**:
   - Component variants are actively harvested from live URLs in `expanded_sites.json` rather than static placeholders.
3. **Real In-App WebView Sandbox**:
   - The Flutter frontend loads real, fully compiled HTML/CSS bundles generated dynamically by `layout-service`, complete with functional CSS grid layouts, semantic JSON-LD tags, and live WhatsApp click-to-chat links.
4. **Real Container Orchestration**:
   - Services communicate via real Docker bridge networks (`docker-compose.dev.yml`) with actual health checks and environment configurations.

---

## 48-Hour Real Implementation Sprint

### Day 1: Real Flutter Chat Shell + WebView Sandbox + Drawer
- **Task 1**: Build `ChatScreen` and `VoiceFrontDrawer` (housing real user session state and fetched storefront lists).
- **Task 2**: Integrate `webview_flutter` to render live HTML bundles received from backend layout generation.
- **Task 3**: Connect Flutter HTTP client directly to Docker backend endpoints (`/v1/nlp/extract`, `/v1/layout/generate`).

### Day 2: Real Backend Orchestration & Live Pipeline Verification
- **Task 1**: Unify backend API routes so chat messages trigger real Groq LLM prompt extraction and live Jinja2 template rendering.
- **Task 2**: Spin up Docker containers (`docker-compose up --build`) with real API keys.
- **Task 3**: Execute end-to-end live testing (Type prompt in app chat -> real Llama-3 extraction -> real Jinja2 render -> real WebView preview in app).
