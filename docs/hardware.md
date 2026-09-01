# VoiceStorefront — Team Hardware & Local Dev Adaptations

**Superseded by `inference_hosting_plan.md`:** the team now runs Whisper and Llama-3 through
Groq's free API, not locally. Everything below about per-person VRAM limits for running these
models locally is no longer the operative plan — kept here as context for why that decision was
made (the mismatch across these 4 machines is exactly what pushed the team toward Groq), and
because IndicBERT/CodeBERT (small, local, CPU-friendly) and general dev capacity are still
accurately described below.

Actual machine specs per person, and what each one means for how they run this project
locally. Ties into `environment.md` (dev vs prod values) and `deployment.md`/`inference_hosting_plan.md`.
All 4 machines are now accounted for — see the full-team parity check at the bottom.

---

## Summary table

| Person | Role | RAM | Storage | CPU | GPU | Local LLM feasible? | Local Whisper feasible? |
|---|---|---|---|---|---|---|---|
| **Person A** | **Voice-to-text (asr-service)** | **16 GB** | **512 GB** | **Ryzen 5 4600H/5600H** | **GTX 1650, 4 GB VRAM** | **Not needed for this role — no LLM dependency** | **Yes, with `faster-whisper` + quantization — tight but workable** |
| Person B | Understanding (nlp-service) | 16 GB | 512 GB | i5-12500H | RTX 3050, 4 GB VRAM | Small models only (Q4, ≤4B) — not Llama-3-8B/Gemma-2-9B directly | Yes, comfortably (`faster-whisper`) |
| **Person C** | **Page-building (layout-service)** | **16 GB** | **1 TB** | **AMD Ryzen 7 4745HS (assumed — confirm exact model)** | **RTX 4050, 6 GB VRAM** | **Yes — comfortably runs Llama-3-8B/Gemma-2-9B at Q4 (~6 GB)** | **Yes, comfortably** |
| **Person D** | **Quality-check + publish (qa-service + publish-service)** | **8 GB** | **1 TB HDD + 256 GB SSD** | **i5-1135G7 @ 2.40GHz** | **MX350, 2 GB VRAM** | **No — not practical even quantized** | **Not practical locally — use staging** |

---

## Person D — detailed notes

This is the tightest machine on the team, and it happens to sit under the heaviest total
workload (per the earlier work-hour breakdown, ~34% of project hours, concentrated in Phase 4).
The good news: **the qa-service + publish-service role doesn't fundamentally need a GPU** —
Playwright, FAISS (`IndexFlatIP`), and CodeBERT-embedding lookups are all CPU-workable. The
adaptations below are about working *around* the constraints, not questioning the role assignment.

### GPU (MX350, 2 GB VRAM) — treat as effectively no GPU for this project
- Too small even for Whisper large-v3 quantized (~1.5–4 GB minimum) or any local LLM (smallest practical Q4 models start around ~2 GB and climb fast).
- **Don't install faster-whisper/Ollama locally expecting GPU use** — anything that needs Whisper or an LLM (e.g. testing the LLM-assisted repair fallback in `core/repair_engine.py`) should point at the shared staging endpoint (`g4dn.xlarge`, per `deployment.md`) rather than running locally.
- CodeBERT embedding (used in `core/learn_engine.py`) is small enough (~125M params) to run on CPU without real slowdown — no GPU needed for this piece specifically.

### RAM (8 GB) — the real day-to-day constraint
This is tighter than it looks once Docker Compose is involved — Playwright's headless Chromium,
Postgres, Redis, and the qa-service process itself all competing for 8 GB will cause swapping.
- Don't run the **full** `docker-compose.dev.yml` stack locally day-to-day. Run only what's needed: `docker compose up qa-service` plus Postgres, and skip asr-service/nlp-service/layout-service containers unless actively debugging cross-service integration — point at a shared dev deployment of those instead when just testing qa-service in isolation.
- Close Chromium/browser tabs before running Playwright test suites — headless Chromium itself needs a few hundred MB per instance, and the 5-viewport-width test run (`test_wcag_compliance.py`) launches multiple render passes.
- Consider a lightweight Postgres alternative for pure local iteration (e.g. a local SQLite fixture for unit tests) and reserve real Postgres-via-Docker for integration test runs only.

### Storage (1 TB HDD + 256 GB SSD) — use the split deliberately
- Put the actual working repo, Docker images, and the FAISS index on the **256 GB SSD** — repeated Playwright renders and Docker image layer access are I/O-heavy, and HDD latency will make local dev noticeably slower.
- Use the 1 TB HDD for anything large and infrequently accessed: archived QA test logs, the constraint-rules dataset backups, recorded pilot-phase audio samples if the team ends up retaining any.

### CPU (i5-1135G7) — adequate for this role
- Fine for Playwright rendering, constraint-graph checks, and FAISS lookups. No changes needed here.

### Net effect on Person D's task list
No change to *what* Person D builds (`sort_engine.py`, `detect_engine.py`, `repair_engine.py`,
`learn_engine.py`, `s3_uploader.py` — see `person_d_qa_publish.md`). The change is *where* the
Whisper/LLM-dependent parts of testing happen: locally for anything CPU-bound, against the
shared staging GPU box for anything that needs Whisper or an LLM. Flag this early — Person D
will need reliable access to that staging endpoint from Phase 3 onward, more than anyone else
on the team given this hardware.

---

## Person A — detailed notes

The voice-to-text role is the one that benefits most from iterating on Whisper repeatedly, so
this GPU matters more here than for Person B or D.

### GPU (GTX 1650, 4 GB VRAM) — workable, same tier as Person B, not the same as full FP16
- Same constraint as Person B: fine for Whisper large-v3 via `faster-whisper` with INT8 quantization (~1.5–4 GB), **not** viable for the stock FP16 path (~10 GB).
- No local LLM dependency in this role, so the 4 GB ceiling doesn't bite anywhere else — `whisper_engine.py` and `language_detect.py` (IndicLID) are the only GPU-touching pieces Person A owns.
- **LoRA fine-tuning Whisper on the retail-domain recordings (Phase 3, step 55) is the one place this GPU will likely struggle** — LoRA fine-tuning still needs headroom beyond pure inference (gradients + optimizer state on top of the base model). Plan to run that specific fine-tuning step on the shared staging GPU box or a rented instance, not this laptop — treat local as inference/testing only, fine-tuning as a staging job.

### RAM/Storage/CPU — adequate
- 16 GB RAM and a 6-core Ryzen are both fine for this role; no changes needed.
- 512 GB storage is enough for the Common Voice subset + retail-domain recordings (`data/seed/`), but keep an eye on it once the 500–1,000 retail samples are collected — audio datasets add up faster than code ever does.

---



- RAM/storage/CPU are all adequate for the nlp-service role.
- GPU (RTX 3050, 4 GB VRAM) can run Whisper comfortably and small quantized LLMs (~3B class), but not Llama-3-8B or Gemma-2-9B at their normal Q4 size (~6 GB) — use a smaller model (Llama-3.2-3B-Instruct or Phi-3-mini) for local iteration, and validate final prompt/schema behavior against the real 8B/9B model on staging before Phase 3 wraps.

---

## Person C — detailed notes

Ironically has the strongest machine on the team for the role that needs it least — layout-service
is CPU/rendering-bound (Jinja2, TF-IDF classifier, CSS), not GPU-bound. Worth turning this spare
capacity into a team asset rather than letting it sit idle.

### GPU (RTX 4050, 6 GB VRAM) — not needed for this role, but useful to the team
- Layout-service itself never touches Whisper or an LLM directly, so this GPU is idle relative to Person C's own task list.
- **Practical suggestion:** since 6 GB VRAM comfortably fits Llama-3-8B/Gemma-2-9B at Q4 (~6 GB) — more than Person A or B's 4 GB cards can do — Person C's machine is the best candidate to run a **local shared Ollama instance** that Person B or D can point at during early dev, before the staging GPU box (`g4dn.xlarge`) is provisioned or when staging is under load. This isn't a requirement, just the highest-leverage use of hardware the team already owns.

### RAM/Storage/CPU — comfortably adequate
- 16 GB RAM, 1 TB storage, and a Ryzen 7-class CPU cover this role with room to spare — no changes needed, and enough headroom to run the full `docker-compose.dev.yml` stack locally without the swapping concerns Person D has.

---

## Full-team parity check (all 4 machines now known)

| Constraint | Who has it | Mitigation already in place |
|---|---|---|
| Can't run Llama-3-8B/Gemma-2-9B at native Q4 size locally | Person A (4 GB), Person B (4 GB), Person D (2 GB) | Use a smaller model (3B class) locally, validate against staging before Phase 3 closes |
| Can't run Whisper comfortably even quantized | Person D only (2 GB) | Use shared staging endpoint instead of local Whisper |
| RAM tight enough to cause Docker/Playwright swapping | Person D only (8 GB) | Run partial stack locally, not the full compose file |
| Spare GPU headroom the team isn't using | Person C (6 GB) | Candidate to host a local shared Ollama instance for the team |

**Bottom line:** three of four machines are below what the design docs assume for local LLM
work (all but Person C), and one machine (Person D's) is below what's assumed for local Whisper
work too. This isn't a reason to change the architecture — it's a reason to make sure the shared
staging GPU box is set up and everyone has access to it **before Phase 2 wraps**, not treated as
a "nice to have" that gets provisioned whenever someone gets around to it. Given Person D's
machine is both the most constrained and, per the work-hour breakdown, the most heavily loaded
role later in the project, they should be the first person confirmed with working staging access.

