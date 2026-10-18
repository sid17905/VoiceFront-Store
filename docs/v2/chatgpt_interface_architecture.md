# ChatGPT-Like Conversational Interface Architecture for VoiceFront-Store

## 1. Overview
Transforming VoiceFront-Store from a rigid form-based/record-based UI into a fluid, conversational ChatGPT-like interface requires unifying text and voice inputs into a continuous chat stream. Users type or speak their retail requirements ("*Create a boutique called Urban Threads with shirts for 799*"), and Tony processes intents incrementally, streaming back questions, confirmations, or live website previews directly within the chat bubble.

---

## 2. Architecture & Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│  CLIENT INTERFACE (Flutter Mobile & Next.js Web)             │
│  • Chat Bubble Stream (User Text / Audio Recording)         │
│  • Live Storefront Preview Card (Floating / Split View)     │
└─────────────────────────────────────────────────────────────┘
                               ↓ (WebSocket / HTTP Streaming)
┌─────────────────────────────────────────────────────────────┐
│  CONVERSATIONAL CHAT GATEWAY (New Service / Gateway Layer)  │
│  • Manages session state & conversation history             │
│  • Routes intents to NLP / ASR                              │
└─────────────────────────────────────────────────────────────┘
          ↓                                           ↓
┌───────────────────────┐                 ┌───────────────────────┐
│  ASR SERVICE (8001)   │                 │  NLP SERVICE (8002)   │
│  • Voice Audio Input  │───────────────> │  • Zero-shot Llama-3  │
└───────────────────────>                 │  • Extracts/Updates   │
                                          │    StorefrontSpec     │
                                          └───────────────────────┘
                                                      ↓
                                          ┌───────────────────────┐
                                          │ LAYOUT SERVICE (8003) │
                                          │ • Renders HTML Preview│
                                          └───────────────────────┘
```

---

## 3. UI/UX Specifications (Mobile & Web)

### Layout Structure
- **Split View (Tablet/Web)** or **Tabbed Sheet (Mobile)**:
  - **Left / Top**: Chat Stream (similar to ChatGPT or Claude web UI).
  - **Right / Bottom Sheet**: Real-time interactive Storefront Preview (updates live as parameters are extracted).

### Chat Features
1. **Multi-modal Input**: Mic button for voice recording (hits ASR) + Text box for prompt input.
2. **Interactive Cards**: When NLP extracts products/prices, render interactive confirmation cards ("Is this correct? [Confirm] [Edit]").
3. **Instant Preview Widget**: Clicking a generated storefront opens the full responsive view inside the app.

---

## 4. Potential Concerns & Mitigations

1. **State Drift / Partial Extractions**:
   - *Concern*: Users provide info in multiple messages ("Add shirts for 799" -> "Also add pants for 999").
   - *Mitigation*: Maintain state session in Redis / FastAPI memory holding the accumulated `StorefrontSpec` across turns. Each turn sends `[Existing Spec + New Prompt]` to Llama-3 to merge attributes.
2. **Latency of Full Pipeline (NLP → Layout → QA)**:
   - *Concern*: Running the full render pipeline on every single chat message might be sluggish.
   - *Mitigation*: Debounce layout rendering until intent confidence is high or user explicitly asks to preview/publish.
3. **Token Costs**:
   - *Concern*: Sending full chat history to Groq on every turn.
   - *Mitigation*: Summarize conversation history or maintain only the rolling `StorefrontSpec` object plus the latest user prompt.
