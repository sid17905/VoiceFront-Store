"""S4 — the scrape endpoint must not become an SSRF proxy."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "packages"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from common_utils.url_guard import UnsafeURL, assert_safe_url  # noqa: E402

BLOCKED = [
    "file:///etc/passwd",
    "gopher://example.com/",
    "ftp://example.com/",
    "http://127.0.0.1/",
    "http://localhost/",
    "http://10.0.0.1/",
    "http://192.168.1.1/",
    "http://169.254.169.254/latest/meta-data/",
    "http://[::1]/",
    "http://0.0.0.0/",
    "http://user:pass@example.com/",
    "http://example.com:22/",
    "http://example.com:8080/",
    "not-a-url",
    "",
]


@pytest.mark.parametrize("url", BLOCKED)
def test_blocked_urls(url):
    with pytest.raises(UnsafeURL):
        assert_safe_url(url)


def test_public_https_is_allowed():
    # example.com resolves to a public address in normal environments.
    try:
        assert assert_safe_url("https://example.com/") == "https://example.com/"
    except UnsafeURL as exc:  # offline CI without DNS
        pytest.skip(f"no DNS: {exc}")
