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
    from common_utils.validators import safe_child, safe_version_id
except ImportError:  # pragma: no cover
    from pathlib import Path as _Path
    import re as _re

    class QaViolationError(Exception):
        def __init__(self, error_code: str, message: str):
            self.error_code = error_code
            self.message = message
            super().__init__(f"{error_code}: {message}")

    _VERSION_RE = _re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

    def safe_version_id(value: str) -> str:
        if not _VERSION_RE.fullmatch(value or ""):
            raise ValueError(f"invalid version_id: {value!r}")
        return value

    def safe_child(base: _Path, filename: str) -> _Path:
        base = base.resolve()
        candidate = (base / filename).resolve()
        if candidate != base and base not in candidate.parents:
            raise ValueError(f"path escapes base directory: {filename!r}")
        return candidate


router = APIRouter(prefix="/v1/qa", tags=["qa"])

SEED_BUNDLES_DIR = Path(__file__).resolve().parents[3] / "data" / "seed" / "rendered_bundles"


# ---------------------------------------------------------------------------
# Request/response models -- shapes must match api_contracts.md exactly
# ---------------------------------------------------------------------------

class QaRunRequest(BaseModel):
    version_id: str | None = None
    html: str | None = None
    auto_repair: bool = False


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
    """Resolve a seed bundle by validated version id.

    I-S3: version_id never reaches the filesystem unchecked.
    """
    try:
        safe_version_id(version_id)
        fixture_path = safe_child(SEED_BUNDLES_DIR, f"{version_id}.html")
    except ValueError as exc:
        raise QaViolationError("QA_INVALID_REQUEST", str(exc)) from exc
    if not fixture_path.exists():
        raise QaViolationError(
            "QA_VERSION_NOT_FOUND",
            f"No bundle found for version_id={version_id}. Phase 1 resolves bundles "
            f"against seed fixtures at {SEED_BUNDLES_DIR}/{{version_id}}.html -- real "
            "storefront_versions/S3 lookup lands once layout-service is producing "
            "real output (Phase 2, see milestones.md).",
        )
    return fixture_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.post("/run", response_model=QaRunResponse)
def run_qa(request: QaRunRequest) -> QaRunResponse:
    if request.html:
        html = request.html
    elif request.version_id:
        html = _load_bundle_html(request.version_id)
    else:
        raise QaViolationError("QA_INVALID_REQUEST", "Either version_id or html must be provided")

    rules = load_rules()
    ranked_rules = rank_failure_risk(rules)
    del ranked_rules

    start = time.monotonic()
    violations = detect_violations(html)
    elapsed_ms = (time.monotonic() - start) * 1000

    repaired_count = 0
    avg_repair_latency_ms = None
    if request.auto_repair and violations:
        from core.repair_engine import repair_violations
        t0_rep = time.monotonic()
        repair_results = repair_violations(violations, html)
        repair_elapsed = (time.monotonic() - t0_rep) * 1000
        repaired_count = sum(1 for r in repair_results if r.was_repaired)
        if repaired_count > 0:
            avg_repair_latency_ms = repair_elapsed / repaired_count
            for r in repair_results:
                if r.repaired_html and r.repaired_html != html:
                    html = r.repaired_html
            violations = detect_violations(html)

    total = len(violations)
    passed = total == 0

    status = "PASSED" if passed else ("REPAIRED" if repaired_count > 0 else "FAILED")

    qa_report = QaReportOut(
        passed=passed,
        total_violations=total,
        repaired_count=repaired_count,
        avg_repair_latency_ms=avg_repair_latency_ms,
        violations=[QaViolationOut(**v.to_api_dict()) for v in violations],
    )

    _ = (elapsed_ms,)

    return QaRunResponse(qa_report=qa_report, status=status)
