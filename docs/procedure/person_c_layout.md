# Person C — Page-Building (layout-service)

Owns: `services/layout-service/` — everything between a `StorefrontSpec` in and a rendered
HTML/CSS/JS bundle out. Read `Architect.md` (L4 section) and `data.md` for the "why." Note:
this role never touches Whisper or the LLM directly — nothing here changed when the team moved
to Groq-hosted inference (`inference_hosting_plan.md`). Your GPU is genuinely idle for your own
task list; `hardware.md` has an optional (not required) idea for putting it to use for the team.

---

## Phase 0 — Setup

- [ ] Pull the repo once scaffolded; confirm Docker Compose runs on your machine.
- [ ] Copy `services/layout-service/.env.example` to `.env` per `environment.md` (`LAYOUT_TEMPLATE_DIR`, `LAYOUT_CATEGORIES`).
- [ ] Confirm you can hit your own stub service's root endpoint once it's in the compose file.
- [ ] Sign off in writing that you own `layout-service` (and, by default, most of `apps/web`'s look-and-feel since you're closest to the rendered output).

## Phase 1 — Foundation

**Shared, do this with the team first:**
- [ ] Sit in on the `StorefrontSpec v1.0` schema review — you're the one turning it into a real page, so flag now if any field is ambiguous for layout purposes (e.g. is `hours` one string or a structured list — you need to know before you template it).

**Your own work:**
- [ ] Pick the first category to build (recommended: food — richest use of the product grid) and hand-build its Jinja2 template in `services/layout-service/templates/`.
- [ ] Write `services/layout-service/core/palette_engine.py` — category → colour palette lookup, at least for this one category to start.
- [ ] Write `services/layout-service/core/renderer.py` — Jinja2 render, **confirm autoescaping is on** (this is a security control per `security.md`, not just a style choice — never disable it).
- [ ] Stub `services/layout-service/core/template_classifier.py` to always return the food template for now — the real k-NN classifier comes in Phase 3 once more templates exist.
- [ ] Write `services/layout-service/routers/generate.py` wiring: template_classifier → palette_engine → renderer, matching `api_contracts.md` (`POST /v1/layout/generate`).

## End of Phase 1 checkpoint
- [ ] You can take a sample `StorefrontSpec` JSON fixture and produce a real rendered food-category page from it.
- [ ] Confirm with Person B that the `StorefrontSpec` shape you're consuming matches exactly what they're producing — mismatches here are the most common Phase 1→2 bug.
