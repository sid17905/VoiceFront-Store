"""
services/qa-service/core/sort_engine.py

L5 SORT phase (Architect.md). Ranks rules/sections by failure-probability so
DETECT spends its budget where violations are historically likely -- this is
what the framework attributes the 38% compute reduction to.

PHASE 1 SCOPE (person_d_qa_publish.md): pass-through stub. Real logic doesn't
start until Phase 3 (procedure_plan.md step 55) -- "start with a simple
heuristic ranking by historical rule-failure frequency; the full model can
come later." Building the real ranking now would mean tuning against fake
data, since Person C won't have real rendered pages until Phase 2.

Naming: rank_failure_risk() -> JSON field "risk_score" (common_references.md).
"""

from __future__ import annotations


def rank_failure_risk(rules: list[dict]) -> list[dict]:
    """
    PHASE 1: pass-through -- returns rules in their original (file-load) order,
    unranked. detect_engine.py currently checks every rule against every
    viewport regardless of order, so this stub doesn't change DETECT's
    behavior yet; it exists so routers/qa.py can call sort -> detect without
    changing that call site once real ranking lands.

    PHASE 3 TODO: replace with a real heuristic -- e.g. a static weight table
    seeded from which sections fail most often in practice (product grids,
    navbars, map embeds per Architect.md), then order rules so DETECT can
    early-exit or prioritize under a compute/time budget.
    """
    return rules
