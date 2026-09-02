# VoiceStorefront — Inference & Hosting Plan (Final, Simple Version)

One page. This replaces every earlier back-and-forth about GPUs, budgets, and hardware.
If it's not written here, it's not the plan.

---

## The decision

**Use Groq's free API for both Whisper and Llama-3, for everything, all 6 months — except one short validation run in Month 5.**

No AWS GPU box. No local model hosting. No per-person hardware juggling. Everyone's laptop,
regardless of specs, just makes an API call.

---

## What runs where

| Piece | Where it runs | Cost |
|---|---|---|
| Whisper (speech-to-text) | Groq API | Free |
| Llama-3 (schema-fill + repair logic) | Groq API | Free |
| Everything else (qa-service, publish-service, layout-service, nlp-service logic, apps/web) | Your own AWS `t3.micro` + S3 + CloudFront | Free (AWS Free Tier, 12 months) |
| One real self-hosted benchmark run, Month 5 only | Rented GPU box for a few hours | ~$5–10, one time |

**Total project cost: under $20.**

---

## What every teammate does, regardless of laptop specs

1. Get a Groq API key (free, no card needed).
2. Point `ASR_WHISPER_ENDPOINT` and `NLP_LLM_ENDPOINT` in your `.env` at Groq.
3. Never install Whisper or Ollama locally. You don't need to.

That's it. This is why the hardware differences between Person A/B/C/D's laptops stop mattering — nobody is running a model on their own machine anymore.

---

## The one thing to watch

Groq's free tier has per-minute limits (roughly 30 requests/min on Llama). If 4 people test at the same time, you can get throttled. Fix: don't panic, just wait a minute and retry, or stagger who's testing when.

---

## The one honest asterisk, for your mentors

Your submitted framework says Llama-3/Gemma-2 were chosen because they're "self-hostable, no per-token API cost." Using Groq means you're using their hosting, not your own, during dev and the pilot. That's why Month 5 includes one real self-hosted run — it proves the self-hosting claim still holds, without paying for it every day for 6 months. Say this plainly in your report; don't let it come up as a surprise.

---

## What changes in your other docs
- `deployment.md` — drop the "spin up GPU box Month 1" plan. AWS is now CPU-only (`t3.micro`) except for the one Month 5 rental.
- `environment.md` — `NLP_LLM_ENDPOINT` and the ASR endpoint now default to Groq's API, not `localhost` or an AWS box.
- `hardware.md` — the local-model VRAM analysis per person is no longer the operative plan; keep the file for context, but it's superseded by this one.

Say the word and I'll make those three edits now so nothing in your repo still points at the old plan.
