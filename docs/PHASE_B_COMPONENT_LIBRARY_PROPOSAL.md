# Proposal: live component library (Phase B) — NEEDS FULL-TEAM SIGN-OFF BEFORE ANY CODE

Status: DRAFT, not built, not wired into layout-service. This is a scope-change
proposal, the same weight as the StorefrontSpec freeze — don't merge quietly.

## What this would add
layout-service pulls human-reviewed HTML/CSS fragments from a DB table
(below) instead of only the 5 fixed Jinja2 templates, matched to a
StorefrontSpec via the same FAISS-similarity pattern qa-service already uses
in repair_engine.py/learn_engine.py.

## Why this needs a team decision, not just Person D/C building it
- Architect.md is explicit: MVP "explicitly excludes freeform layout
  generation." This proposal is exactly that.
- IP: only human-reviewed/rewritten fragments should ever be servable —
  raw scraped markup never ships to a real user. `review_status` below
  enforces this at the schema level, but the review workflow itself needs
  the team to agree who does it and when.
- Touches layout-service (Person C) and packages/schemas (shared) — not a
  qa-service-only change.

## Proposed schema addition (data.md)
```sql
CREATE TABLE component_library (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category        TEXT NOT NULL CHECK (category IN
                      ('food','apparel','electronics','pharmacy','services')),
    section_type    TEXT NOT NULL,   -- nav | hero | product_grid | contact
    html            TEXT NOT NULL,
    css             TEXT NOT NULL,
    source_url      TEXT,            -- design-reference provenance, nullable if original
    review_status   TEXT NOT NULL DEFAULT 'PENDING'
                      CHECK (review_status IN ('PENDING','APPROVED','REJECTED')),
    reviewed_by     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```
Only rows with `review_status = 'APPROVED'` are ever eligible to be pulled by
layout-service — this is the enforcement point for "never serve raw scraped
markup."

## Proposed JSON Schema (packages/schemas/component_library.schema.json)
See the sibling file in this delivery — mirrors the SQL table above so
Pydantic/TS types generate identically, per common_references.md convention.

## What's explicitly NOT decided yet
- Matching algorithm details (cosine threshold? same 0.87 as repair_engine.py?)
- Who performs the human review step, and on what cadence
- Whether this ships in the 6-month MVP window at all, or moves to v2.0
  (VoiceFront_Store_PROJECT_ABSTRACT.md §4 already lists "custom layout
  generation" as a natural v2.0 candidate)

## Recommendation
Bring this to the next full-team sync. If approved, it's Person C's
implementation lead (layout-service owns rendering), with Person D
supporting on the FAISS-matching piece since qa-service already has that
pattern built.
