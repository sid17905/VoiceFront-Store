"""P3 — the prefix-isolation check must be able to fail."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

SERVICE = Path(__file__).resolve().parents[1]
if str(SERVICE) not in sys.path:
    sys.path.insert(0, str(SERVICE))

import core.s3_uploader as s3_uploader  # noqa: E402


def policy_client(policy: dict | None) -> MagicMock:
    client = MagicMock()
    if policy is None:
        from botocore.exceptions import ClientError
        client.get_bucket_policy.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucketPolicy"}}, "GetBucketPolicy")
    else:
        client.get_bucket_policy.return_value = {"Policy": json.dumps(policy)}
    return client


def public_policy(resource: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": resource,
        }],
    }


def test_missing_policy_is_false():
    with patch("core.s3_uploader._s3_client", return_value=policy_client(None)):
        assert s3_uploader.verify_prefix_isolation() is False


def test_prefix_scoped_policy_is_true():
    bucket = s3_uploader.S3_BUCKET
    with patch("core.s3_uploader._s3_client",
               return_value=policy_client(public_policy(f"arn:aws:s3:::{bucket}/storefronts/*"))):
        assert s3_uploader.verify_prefix_isolation() is True


def test_bucket_wide_read_is_false():
    bucket = s3_uploader.S3_BUCKET
    with patch("core.s3_uploader._s3_client",
               return_value=policy_client(public_policy(f"arn:aws:s3:::{bucket}/*"))):
        assert s3_uploader.verify_prefix_isolation() is False


def test_whole_bucket_arn_is_false():
    bucket = s3_uploader.S3_BUCKET
    with patch("core.s3_uploader._s3_client",
               return_value=policy_client(public_policy(f"arn:aws:s3:::{bucket}"))):
        assert s3_uploader.verify_prefix_isolation() is False


def test_public_read_outside_prefix_is_false():
    bucket = s3_uploader.S3_BUCKET
    with patch("core.s3_uploader._s3_client",
               return_value=policy_client(public_policy(f"arn:aws:s3:::{bucket}/internal/*"))):
        assert s3_uploader.verify_prefix_isolation() is False


def test_private_statement_is_ignored():
    bucket = s3_uploader.S3_BUCKET
    policy = {
        "Statement": [
            {"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject",
             "Resource": f"arn:aws:s3:::{bucket}/storefronts/*"},
            {"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::123:root"},
             "Action": "s3:GetObject", "Resource": f"arn:aws:s3:::{bucket}/internal/*"},
        ]
    }
    with patch("core.s3_uploader._s3_client", return_value=policy_client(policy)):
        assert s3_uploader.verify_prefix_isolation() is True
