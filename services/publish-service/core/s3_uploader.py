"""
services/publish-service/core/s3_uploader.py

Only publish-service writes to S3/CloudFront (flow.md's state-ownership rule).
Security constraint (security.md Sec 3): public READ only on the specific
prefix serving published storefronts (STOREFRONT_PREFIX below) -- everything
else stays private, and no path outside that prefix should ever be
world-readable. No public WRITE access under any circumstance -- only this
service's IAM role/credentials can write at all.

Live URL is only returned after the CloudFront invalidation is CONFIRMED, not
fire-and-forget (integration.md Sec 4) -- so a returned URL is actually
serving the new content, not still showing a stale cached version.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

try:
    from common_utils.exceptions import PublishError
except ImportError:  # pragma: no cover
    class PublishError(Exception):
        def __init__(self, error_code: str, message: str):
            self.error_code = error_code
            self.message = message
            super().__init__(f"{error_code}: {message}")

# Env vars per environment.md — publish-service section
S3_BUCKET = os.environ.get("PUBLISH_S3_BUCKET", "voicestorefront-dev")
CLOUDFRONT_DIST_ID = os.environ.get("PUBLISH_CLOUDFRONT_DIST_ID", "")
AWS_REGION = os.environ.get("PUBLISH_AWS_REGION", "ap-south-1")

# Only files under this prefix are ever made public. Any upload outside this
# prefix (e.g. intermediate/raw assets, if ever added later) must NOT go
# through publish_storefront() below.
STOREFRONT_PREFIX = "storefronts"

# CloudFront invalidation polling
_INVALIDATION_POLL_INTERVAL_SEC = 2
_INVALIDATION_TIMEOUT_SEC = 60


@dataclass
class PublishResult:
    live_url: str
    published_at: str  # ISO 8601 UTC, per api_contracts.md cross-cutting conventions


def _s3_client():
    return boto3.client("s3", region_name=AWS_REGION)


def _cloudfront_client():
    return boto3.client("cloudfront", region_name=AWS_REGION)


def _storefront_key(version_id: str, filename: str = "index.html") -> str:
    """Every published-bundle key lives under STOREFRONT_PREFIX/{version_id}/...
    -- this is the ONLY prefix the bucket policy should grant public read on
    (see infra/terraform/s3_cloudfront.tf for the actual policy).

    I-S3: version_id is validated before it becomes an object key.
    """
    from common_utils.validators import safe_version_id

    return f"{STOREFRONT_PREFIX}/{safe_version_id(version_id)}/{filename}"


def upload_bundle(html_content: str, version_id: str) -> str:
    """
    Upload a single-file HTML bundle for `version_id` to S3 under the public
    storefront prefix. Returns the S3 key.

    Phase 1 scope (person_d_qa_publish.md): confirms the happy-path upload
    works against a dev bucket. CSS/JS-as-separate-files, versioned re-renders,
    etc. are the same pattern extended in Phase 4 once layout-service produces
    multi-file bundles (Architect.md L4: html, css, js, template_id).
    """
    key = _storefront_key(version_id)
    client = _s3_client()
    try:
        client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=html_content.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
            # No ACL set here on purpose -- public read is granted at the
            # BUCKET POLICY level, scoped to STOREFRONT_PREFIX/*, not per-object
            # ACLs (security.md: "public read only on the specific prefix").
        )
    except ClientError as exc:
        raise PublishError("PUBLISH_S3_FAILED", str(exc)) from exc
    return key


def verify_prefix_isolation(test_key: str = "internal/should-stay-private.txt") -> bool:
    """Check that the bucket policy exposes ONLY STOREFRONT_PREFIX publicly.

    Previously this uploaded an object, discarded the response and returned
    True unconditionally — a test that could not fail. It now reads the bucket
    policy and inspects every Allow statement with a public principal:

      - any Resource outside  arn:aws:s3:::<bucket>/storefronts/*  -> False
      - any statement that grants public read on the whole bucket  -> False
      - no policy at all                                            -> False

    Returns True only when every public grant is scoped to the prefix.
    """
    import json as _json

    client = _s3_client()
    try:
        policy_doc = client.get_bucket_policy(Bucket=S3_BUCKET)["Policy"]
    except ClientError:
        return False

    try:
        policy = _json.loads(policy_doc)
    except _json.JSONDecodeError:
        return False

    allowed_prefix = f"arn:aws:s3:::{{bucket}}/{STOREFRONT_PREFIX}/".format(bucket=S3_BUCKET)
    bucket_arn = f"arn:aws:s3:::{S3_BUCKET}"

    for statement in policy.get("Statement", []):
        if statement.get("Effect") != "Allow":
            continue
        principal = statement.get("Principal")
        is_public = principal == "*" or (
            isinstance(principal, dict) and principal.get("AWS") == "*"
        )
        if not is_public:
            continue
        actions = statement.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        if not any(a in ("s3:GetObject", "s3:*", "*") for a in actions):
            continue
        resources = statement.get("Resource", [])
        if isinstance(resources, str):
            resources = [resources]
        for resource in resources:
            if resource == bucket_arn or resource == f"{bucket_arn}/*":
                return False
            if not resource.startswith(allowed_prefix):
                return False

    return True


def invalidate_cloudfront(paths: list[str]) -> str:
    """Create a CloudFront invalidation for the given paths, return the
    invalidation ID so the caller can confirm completion before returning a
    live URL to the user."""
    if not CLOUDFRONT_DIST_ID:
        raise PublishError(
            "PUBLISH_S3_FAILED",  # no dedicated CDN error code in api_contracts.md yet
            "PUBLISH_CLOUDFRONT_DIST_ID is not set (environment.md).",
        )
    client = _cloudfront_client()
    try:
        response = client.create_invalidation(
            DistributionId=CLOUDFRONT_DIST_ID,
            InvalidationBatch={
                "Paths": {"Quantity": len(paths), "Items": paths},
                "CallerReference": f"publish-{int(time.time())}",
            },
        )
        return response["Invalidation"]["Id"]
    except ClientError as exc:
        raise PublishError("PUBLISH_S3_FAILED", str(exc)) from exc


def wait_for_invalidation(invalidation_id: str, timeout_sec: int | None = None) -> bool:
    """Poll until the invalidation completes or timeout_sec elapses. Returns
    True only on confirmed completion -- per integration.md, we do not return
    a live URL on a fire-and-forget invalidation.

    timeout_sec defaults to None and is resolved against the *current* module
    value of _INVALIDATION_TIMEOUT_SEC at call time, not at function-definition
    time -- a plain `= _INVALIDATION_TIMEOUT_SEC` default would bind the value
    once at import and silently ignore any later override (env config reload,
    or a monkeypatch in tests)."""
    if timeout_sec is None:
        timeout_sec = _INVALIDATION_TIMEOUT_SEC
    client = _cloudfront_client()
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        resp = client.get_invalidation(DistributionId=CLOUDFRONT_DIST_ID, Id=invalidation_id)
        if resp["Invalidation"]["Status"] == "Completed":
            return True
        time.sleep(_INVALIDATION_POLL_INTERVAL_SEC)
    return False


def publish_storefront(html_content: str, version_id: str, slug: str, domain: str) -> PublishResult:
    """
    Full publish path per Architect.md L5 / integration.md Sec 4:
    upload -> invalidate -> confirm invalidation -> return live URL.

    P2: the returned URL is derived from the S3 key that was actually written,
    so the URL and the object cannot disagree. `slug` is retained for
    compatibility but only used as a fallback when no domain is supplied.
    """
    key = upload_bundle(html_content, version_id)
    invalidation_id = invalidate_cloudfront([f"/{key}"])

    if not wait_for_invalidation(invalidation_id):
        raise PublishError(
            "PUBLISH_S3_FAILED",
            f"CloudFront invalidation {invalidation_id} did not complete within "
            f"{_INVALIDATION_TIMEOUT_SEC}s -- not returning a live URL until it does.",
        )

    if domain:
        live_url = f"https://{domain}/{key}"
    else:
        live_url = f"/{slug}/index.html"

    return PublishResult(
        live_url=live_url,
        published_at=datetime.now(timezone.utc).isoformat(),
    )
