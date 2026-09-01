"""
services/qa-service/core/repair_engine.py

L5 REPAIR phase (Architect.md). Real logic: embed the violation, match against
the FAISS repair-pattern store (cosine similarity > QA_SIMILARITY_THRESHOLD,
0.87) -> apply the stored patch on a match; on no match, fall back to
LLM-assisted repair via the shared `packages/common-utils/groq_client.py`
(Groq-hosted Llama, same as nlp-service -- NOT a locally-hosted model, which
is genuinely good news given this role's hardware, see hardware.md).

PHASE 1 SCOPE (person_d_qa_publish.md): pass-through stub. Real logic isn't
due until Phase 4 (procedure_plan.md steps 65-69) -- the FAISS index doesn't
exist yet and there's nothing to match against.

Naming: repair_violation() -> JSON field "repairs_applied" (common_references.md).
"""

from __future__ import annotations

from core.detect_engine import Violation


def repair_violation(violation: Violation) -> Violation:
    """
    PHASE 1: pass-through -- returns the violation unmodified, was_repaired
    stays False, repair_source stays None. No FAISS lookup, no Groq call.

    PHASE 4 TODO (procedure_plan.md steps 65-68):
      1. Embed the violation (CodeBERT) and query the FAISS index
         (QA_FAISS_INDEX_PATH, threshold QA_SIMILARITY_THRESHOLD=0.87).
      2. On a match: apply the stored patch_diff, set
         repair_source="faiss_match".
      3. On no match: call the Groq-hosted LLM via groq_client.call_groq_chat()
         to generate a new patch, set repair_source="llm_generated". Expect
         this path to be slower than the original <800ms target, which assumed
         local inference -- see testing.md / QA_MAX_REPAIR_LATENCY_MS.
      4. Re-render the patched section and re-run detect_engine.py on just
         that section (the "detect -> repair -> re-detect" loop in flow.md).
         Only set was_repaired=True if the re-check actually passes.
    """
    return violation


def repair_violations(violations: list[Violation]) -> list[Violation]:
    """Batch wrapper -- Phase 1: applies the pass-through to every violation."""
    return [repair_violation(v) for v in violations]
