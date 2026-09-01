"""
services/qa-service/routers/qa.py

POST /v1/qa/run -- matches api_contracts.md exactly.

PHASE 1 wiring (procedure_plan.md step 63): sort -> detect only. repair_engine.py
and learn_engine.py exist as stubs (core/repair_engine.py, core/learn_engine.py)
but are NOT called from this router yet -- that wiring is Phase 4. `passed` may
legitimately be False right now; that's expected, not a bug.

Bundle lookup: real layout-service output + Postgres-backed storefront_versions
isn't live until Phase 2 (milestones.md). Until then this router resolves
`version_id` against the local seed fixtures in data/seed/rendered_bundles/ so
DETECT can be exercised end-to-end without waiting on Track C (per the
mitigation milestones.md calls out explicitly for this exact dependency).
"""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from core.detect_engine import detect_violations, load_rules
from core.sort_engine import rank_failure_risk

try:
    from common_utils.exceptions import QaViolationError
except ImportError:  # pragma: no cover
    class QaViolationError(Exception):
        def __init__(self, error_code: str, message: str):
            self.error_code = error_code
            self.message = message
            super().__init__(f"{error_code}: {message}")


router = APIRouter(prefix="/v1/qa", tags=["qa"])

SEED_BUNDLES_DIR = Path(__file__).resolve().parents[3] / "data" / "seed" / "rendered_bundles"


# ---------------------------------------------------------------------------
# Request/response models -- shapes must match api_contracts.md exactly
# ---------------------------------------------------------------------------

class QaRunRequest(BaseModel):
    version_id: str


class QaViolationOut(BaseModel):
    rule_id: str
    severity: str
    viewport_width: int
    was_repaired: bool
    repair_source: str | None = None


class QaReportOut(BaseModel):
    passed: bool
    total_violations: int
    repaired_count: int
    avg_repair_latency_ms: float | None
    violations: list[QaViolationOut]


class QaRunResponse(BaseModel):
    qa_report: QaReportOut
    status: str  # PASSED | FAILED | REPAIRED (common_references.md status enum)


# ---------------------------------------------------------------------------
# Bundle resolution (Phase 1: seed fixtures; Phase 2+: real S3/Postgres lookup)
# ---------------------------------------------------------------------------

def _load_bundle_html(version_id: str) -> str:
    fixture_path = SEED_BUNDLES_DIR / f"{version_id}.html"
    if fixture_path.exists():
        return fixture_path.read_text(encoding="utf-8")
    raise QaViolationError(
        "QA_VERSION_NOT_FOUND",
        f"No bundle found for version_id={version_id}. Phase 1 resolves bundles "
        f"against seed fixtures at {SEED_BUNDLES_DIR}/{{version_id}}.html -- real "
        "storefront_versions/S3 lookup lands once layout-service is producing "
        "real output (Phase 2, see milestones.md).",
    )


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/run", response_model=QaRunResponse)
def run_qa(request: QaRunRequest) -> QaRunResponse:
    html = _load_bundle_html(request.version_id)

    rules = load_rules()
    ranked_rules = rank_failure_risk(rules)  # PHASE 1: pass-through, see sort_engine.py
    del ranked_rules  # not yet consumed by detect_engine.py -- Phase 3 wires this through

    start = time.monotonic()
    violations = detect_violations(html)
    elapsed_ms = (time.monotonic() - start) * 1000

    total = len(violations)
    critical_count = sum(1 for v in violations if v.severity == "critical")
    # PHASE 1: no repair pass yet, so "passed" only when there are zero
    # violations outright -- once repair_engine.py is wired in Phase 4, this
    # becomes "0 critical AND minor count under the MVP budget" per Architect.md.
    passed = total == 0

    status = "PASSED" if passed else "FAILED"

    qa_report = QaReportOut(
        passed=passed,
        total_violations=total,
        repaired_count=0,  # PHASE 1: repair not wired in yet
        avg_repair_latency_ms=None,  # PHASE 1: nothing repaired to time
        violations=[QaViolationOut(**v.to_api_dict()) for v in violations],
    )

    # avg detect latency isn't part of the wire contract, but useful in logs
    # while validating the <800ms/violation and TTL targets later (testing.md).
    _ = (elapsed_ms, critical_count)

    return QaRunResponse(qa_report=qa_report, status=status)
