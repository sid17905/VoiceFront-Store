"""
services/publish-service/routers/publish.py

POST /v1/publish -- matches api_contracts.md.

Precondition (api_contracts.md): the caller must have already received
qa_report.passed == true, but this service RE-VALIDATES server-side against
the qa_reports table rather than trusting the client (never take the
frontend's word for it -- a stale/replayed request shouldn't be able to
publish something that failed QA).

Phase 1 scope: the qa_reports table + real Postgres wiring isn't live yet
(that's Track D's Phase 3-4 integration work once qa-service is producing
real reports against real bundles). This router's re-validation hook is
written now so the "never trust the client" shape is correct from day one,
even while its data source is still a stub.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from core.s3_uploader import publish_storefront

try:
    from common_utils.exceptions import PublishError
    from common_utils.validators import safe_child, safe_version_id
except ImportError:  # pragma: no cover
    from pathlib import Path as _Path
    import re as _re

    class PublishError(Exception):
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

router = APIRouter(prefix="/v1", tags=["publish"])

PROJECT_DOMAIN = "voicestorefront.app"  # placeholder -- replace with the real
# purchased domain once bought (milestones.md Month 1 step: "buy the project
# domain ~$10/year"). CloudFront/DNS wiring lives in deployment.md.


class PublishRequest(BaseModel):
    version_id: str


class PublishResponse(BaseModel):
    live_url: str
    published_at: str


def _server_side_qa_passed_check(version_id: str) -> bool:
    """
    PHASE 1 STUB: qa_reports table isn't wired up yet (Postgres integration
    lands as Track D's other services come online). Returns True unconditionally
    for now so the endpoint is exercisable end-to-end against seed fixtures.

    PHASE 2+ TODO: SELECT passed FROM qa_reports WHERE version_id = %s ORDER BY
    created_at DESC LIMIT 1 -- this is the actual server-side re-validation
    api_contracts.md requires; a client-supplied "trust me, QA passed" is
    explicitly not sufficient.
    """
    return True


def _get_bundle_html(version_id: str) -> str:
    # Same Phase 1 seed-fixture pattern as qa-service/routers/qa.py, kept
    # consistent so both services can be exercised against the same fixtures
    # in data/seed/rendered_bundles/ before real S3-backed bundle storage exists.
    from pathlib import Path

    try:
        safe_version_id(version_id)
        fixture_path = safe_child(
            Path(__file__).resolve().parents[3] / "data" / "seed" / "rendered_bundles",
            f"{version_id}.html",
        )
    except ValueError as exc:
        raise PublishError("PUBLISH_INVALID_REQUEST", str(exc)) from exc
    if not fixture_path.exists():
        raise PublishError("PUBLISH_BUNDLE_NOT_FOUND", f"No bundle fixture for {version_id}")
    return fixture_path.read_text(encoding="utf-8")


@router.post("/publish", response_model=PublishResponse)
def publish(request: PublishRequest) -> PublishResponse:
    if not _server_side_qa_passed_check(request.version_id):
        raise PublishError(
            "PUBLISH_QA_NOT_PASSED",
            f"version_id={request.version_id} has not passed QA server-side.",
        )

    html = _get_bundle_html(request.version_id)
    slug = request.version_id  # Phase 1: version_id as slug; real slugging
    # (shop-name-derived, collision-checked) is a small Phase 2 addition once
    # StorefrontSpec.shop_name is reliably populated.

    result = publish_storefront(html, request.version_id, slug, PROJECT_DOMAIN)
    return PublishResponse(live_url=result.live_url, published_at=result.published_at)
