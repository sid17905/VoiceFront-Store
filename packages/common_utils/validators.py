"""Shared input validators for identifiers that become paths, keys, or URLs.

Invariant I-S3: no user-controlled string reaches a filesystem path, S3 key, or
URL path without passing through these helpers.
"""
from __future__ import annotations

import re
from pathlib import Path

_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")

# Characters that are legal in a slug but dangerous in a path or S3 key.
UNSAFE_SLUG_RE = re.compile(r"[/\\\x00-\x1f]")


class InvalidIdentifier(ValueError):
    """Raised when a caller-supplied identifier is not safe to use."""


def safe_version_id(value: str) -> str:
    """Return `value` if it looks like a version id, else raise.

    Accepts 1-64 chars: letters, digits, underscore, hyphen; must start
    alphanumeric. Rejects empty strings, dot-segments, separators, percent
    encodings, and anything with control characters.
    """
    if not isinstance(value, str) or not _VERSION_RE.fullmatch(value):
        raise InvalidIdentifier(f"invalid version_id: {value!r}")
    return value


def safe_slug(value: str, *, max_length: int = 64) -> str:
    """Return a URL-safe slug derived from `value` (best effort).

    Lowercases, replaces runs of non-alphanumerics with '-', trims hyphens,
    and falls back to 'store' when nothing survives.
    """
    if not isinstance(value, str):
        raise InvalidIdentifier("slug must be a string")
    if UNSAFE_SLUG_RE.search(value):
        raise InvalidIdentifier(f"unsafe characters in slug: {value!r}")
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:max_length]
    return slug or "store"


def safe_child(base: Path, filename: str) -> Path:
    """Resolve `base/filename` and assert it stays inside `base`.

    Rejects absolute components, any `..` segment (even one that resolves back
    inside the base), and symlink escapes.
    """
    if not isinstance(filename, str) or not filename:
        raise InvalidIdentifier("filename must be a non-empty string")
    if "\x00" in filename:
        raise InvalidIdentifier("NUL byte in filename")
    candidate_input = Path(filename)
    if candidate_input.is_absolute() or candidate_input.drive:
        raise InvalidIdentifier(f"absolute path not allowed: {filename!r}")
    if any(part == ".." for part in candidate_input.parts):
        raise InvalidIdentifier(f"parent segment not allowed: {filename!r}")

    base = Path(base).resolve()
    candidate = (base / filename).resolve()
    if candidate != base and base not in candidate.parents:
        raise InvalidIdentifier(f"path escapes base directory: {filename!r}")
    return candidate
