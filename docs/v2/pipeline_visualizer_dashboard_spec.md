# Pipeline Visualizer & Internal Working Dashboard Spec

## 1. Concept: Live Pipeline Visualizer
To showcase the internal engineering of VoiceFront-Store (and leverage our existing `docs/procedure/pipeline-visualizer.html` assets), we build a **Developer / Inspector Mode Dashboard** accessible via a web interface or a toggle in app settings.

---

## 2. Key Features of the Working Dashboard

### A. Live 5-Layer Pipeline Tracer
When a user submits a prompt or audio file, the dashboard visually lights up each layer in real-time with latency and status metrics:
1. **L1/L2 (ASR & Normalization)**: Shows audio waveform, waveform length, transcription confidence score, and raw text.
2. **L3 (NLP & Schema Extraction)**: Displays the Groq LLM system prompt, token count, retry attempts, and the parsed `StorefrontSpec` JSON tree.
3. **L4 (Layout & Component Assembly)**: Visualizes selected category, active palette hex codes, matched component variants (with provenance source URLs), and rendered HTML size.
4. **L5 (QA & Accessibility Audit)**: Live breakdown of Playwright viewport testing, axe-core WCAG 2.2 AA violations found, and structural check results.
5. **L6 (Publishing & CDN)**: S3 upload status and CloudFront invalidation confirmation.

### B. REA & Scrapling Intelligence Inspector
- A dedicated tab showing scraped reference sites, extracted component snippets, and REA behavioral insights.

---

## 3. Implementation Plan
- **Backend Endpoint**: Aggregate internal service metrics into a single WebSocket/SSE stream at `/v1/pipeline/trace/{session_id}`.
- **Frontend**: Embed or serve a lightweight HTML/JS dashboard (adapting `docs/procedure/pipeline-visualizer.html`) that connects to the backend tracer.
