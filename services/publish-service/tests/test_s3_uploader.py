"""
Per testing.md: unit tests mock I/O. boto3's S3/CloudFront clients are
patched here so these tests never touch real AWS -- that's what the Phase 1
"confirm a file uploads... against a dev bucket" checklist item is for
(person_d_qa_publish.md), done manually/once against a real dev bucket, not
on every test run.
"""

from unittest.mock import MagicMock, patch

import pytest

import core.s3_uploader as s3_uploader
from core.s3_uploader import (
    PublishResult,
    _storefront_key,
    invalidate_cloudfront,
    publish_storefront,
    upload_bundle,
)


def test_storefront_key_is_scoped_to_public_prefix():
    key = _storefront_key("abc-123")
    assert key == "storefronts/abc-123/index.html"
    assert key.startswith(s3_uploader.STOREFRONT_PREFIX + "/")


def test_upload_bundle_calls_put_object_with_expected_args():
    fake_client = MagicMock()
    with patch("core.s3_uploader._s3_client", return_value=fake_client):
        key = upload_bundle("<html>hi</html>", "version-1")

    assert key == "storefronts/version-1/index.html"
    fake_client.put_object.assert_called_once()
    _, kwargs = fake_client.put_object.call_args
    assert kwargs["Key"] == "storefronts/version-1/index.html"
    assert kwargs["ContentType"].startswith("text/html")
    assert b"hi" in kwargs["Body"]
    # No ACL should be set at the object level -- public read is a bucket-policy
    # concern scoped to STOREFRONT_PREFIX, per security.md.
    assert "ACL" not in kwargs


def test_upload_bundle_raises_publish_error_on_client_error():
    from botocore.exceptions import ClientError

    fake_client = MagicMock()
    fake_client.put_object.side_effect = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "PutObject"
    )
    with patch("core.s3_uploader._s3_client", return_value=fake_client):
        with pytest.raises(Exception) as exc_info:
            upload_bundle("<html></html>", "version-2")
    assert "PublishError" in exc_info.typename or hasattr(exc_info.value, "error_code")


def test_invalidate_cloudfront_requires_dist_id(monkeypatch):
    monkeypatch.setattr(s3_uploader, "CLOUDFRONT_DIST_ID", "")
    with pytest.raises(Exception):
        invalidate_cloudfront(["/storefronts/x/index.html"])


def test_invalidate_cloudfront_calls_create_invalidation(monkeypatch):
    monkeypatch.setattr(s3_uploader, "CLOUDFRONT_DIST_ID", "DIST123")
    fake_client = MagicMock()
    fake_client.create_invalidation.return_value = {"Invalidation": {"Id": "INV1"}}
    with patch("core.s3_uploader._cloudfront_client", return_value=fake_client):
        inv_id = invalidate_cloudfront(["/storefronts/x/index.html"])
    assert inv_id == "INV1"
    fake_client.create_invalidation.assert_called_once()


def test_publish_storefront_returns_live_url_only_after_invalidation_confirmed(monkeypatch):
    monkeypatch.setattr(s3_uploader, "CLOUDFRONT_DIST_ID", "DIST123")
    fake_s3 = MagicMock()
    fake_cf = MagicMock()
    fake_cf.create_invalidation.return_value = {"Invalidation": {"Id": "INV1"}}
    fake_cf.get_invalidation.return_value = {"Invalidation": {"Status": "Completed"}}

    with patch("core.s3_uploader._s3_client", return_value=fake_s3), \
         patch("core.s3_uploader._cloudfront_client", return_value=fake_cf):
        result = publish_storefront("<html></html>", "v1", "sharma-store", "voicestorefront.app")

    assert isinstance(result, PublishResult)
    assert result.live_url == "https://voicestorefront.app/sharma-store"
    assert result.published_at  # ISO timestamp set


def test_publish_storefront_fails_closed_if_invalidation_never_completes(monkeypatch):
    monkeypatch.setattr(s3_uploader, "CLOUDFRONT_DIST_ID", "DIST123")
    monkeypatch.setattr(s3_uploader, "_INVALIDATION_TIMEOUT_SEC", 0)  # don't actually wait in tests
    fake_s3 = MagicMock()
    fake_cf = MagicMock()
    fake_cf.create_invalidation.return_value = {"Invalidation": {"Id": "INV1"}}
    fake_cf.get_invalidation.return_value = {"Invalidation": {"Status": "InProgress"}}

    with patch("core.s3_uploader._s3_client", return_value=fake_s3), \
         patch("core.s3_uploader._cloudfront_client", return_value=fake_cf):
        with pytest.raises(Exception):
            publish_storefront("<html></html>", "v2", "slug", "voicestorefront.app")
