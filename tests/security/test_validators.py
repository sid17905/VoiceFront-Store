"""S3 — identifiers used as paths, S3 keys and URL paths must be validated."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "packages"
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from common_utils.validators import (  # noqa: E402
    InvalidIdentifier,
    safe_child,
    safe_slug,
    safe_version_id,
)

BAD_IDS = [
    "", " ", "../x", "..\\x", "a/b", "a\\b", ".", "..", "/abs", "a%2e%2e%2fb",
    "a" * 65, "x\x00y", "-leading-hyphen", "with space", "semi;colon",
]

GOOD_IDS = ["fixture-good", "fixture-bad", "v1", "2026-10-18", "a", "A_b-c9"]


@pytest.mark.parametrize("bad", BAD_IDS)
def test_bad_version_ids_rejected(bad):
    with pytest.raises(InvalidIdentifier):
        safe_version_id(bad)


@pytest.mark.parametrize("good", GOOD_IDS)
def test_good_version_ids_accepted(good):
    assert safe_version_id(good) == good


def test_safe_child_stays_inside(tmp_path):
    (tmp_path / "ok.html").write_text("x", encoding="utf-8")
    assert safe_child(tmp_path, "ok.html").exists()


@pytest.mark.parametrize("bad", ["../ok.html", "..\\ok.html", "/etc/passwd", "sub/../ok.html"])
def test_safe_child_blocks_escape(tmp_path, bad):
    with pytest.raises(InvalidIdentifier):
        safe_child(tmp_path, bad)


def test_slug_is_url_safe():
    assert safe_slug("Krishna Sweets") == "krishna-sweets"
    assert safe_slug("!!!") == "store"


def test_slug_rejects_separators():
    with pytest.raises(InvalidIdentifier):
        safe_slug("a/b")
