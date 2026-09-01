"""
services/qa-service/core/learn_engine.py

L5 LEARN phase (Architect.md). Real logic: every *successfully applied* repair
(verified by re-running DETECT on the patched section, per flow.md's loop 2)
gets CodeBERT-embedded and written into the FAISS index (IndexFlatIP, data.md
Sec 4). This is the entire continual-learning loop for the MVP -- rule
accumulation, not model fine-tuning (Architect.md's cross-cutting note; say
this precisely if a panel member probes it).

State ownership (flow.md): this file is the ONLY writer to the FAISS index --
no other service touches it, even for reads.

PHASE 1 SCOPE (person_d_qa_publish.md): no-op stub. There's nothing to learn
from yet -- repair_engine.py doesn't repair anything until Phase 4, and the
FAISS index itself doesn't exist until then either.

Naming: vectorize_rule() (common_references.md).
"""

from __future__ import annotations

from core.detect_engine import Violation


def vectorize_rule(repaired_violation: Violation) -> None:
    """
    PHASE 1: no-op. Confirmed-repaired violations aren't a thing yet in this
    phase, so this function is never meaningfully called -- it exists so
    routers/qa.py's wiring (sort -> detect -> repair -> learn) doesn't need
    to change shape once Phase 4 lands.

    PHASE 4 TODO (procedure_plan.md step 68):
      1. Confirm the violation actually carries a survived-re-detection repair
         (repair_source set, and a re-run of detect_engine.py on the patched
         section no longer reports it).
      2. Embed the patch (CodeBERT, ~125M params -- CPU-workable, see
         hardware.md's note on Person D's machine specifically).
      3. Write {rule_id, violation_type, patch_diff, times_reused, created_at}
         into the FAISS index at QA_FAISS_INDEX_PATH.
      4. Never write a repair that wasn't confirmed -- failed repairs are
         dropped here, not retried into the index (flow.md).
    """
    return None


def vectorize_rules(repaired_violations: list[Violation]) -> None:
    """Batch wrapper -- Phase 1: no-op for every item."""
    for v in repaired_violations:
        vectorize_rule(v)
