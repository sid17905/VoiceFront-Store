"""SSRF guard for the layout scraper.

Invariant I-S4. Rejects non-HTTP schemes, embedded credentials, non-80/443
ports, and any hostname that resolves to private, loopback, link-local,
reserved, multicast, or unspecified addresses.

Limitation (documented, not hidden): DNS can be re-bound between this check
and the browser fetch. Mitigations are described in
docs/REMEDIATION_PLAN_TO_A_PLUS.md S4.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443}


class UnsafeURL(ValueError):
    pass


def assert_safe_url(url: str) -> str:
    """Return `url` if it is safe to fetch, else raise UnsafeURL."""
    if not isinstance(url, str) or not url:
        raise UnsafeURL("empty url")

    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeURL(f"scheme not allowed: {parsed.scheme!r}")
    if parsed.username or parsed.password:
        raise UnsafeURL("credentials in URL are not allowed")
    host = parsed.hostname
    if not host:
        raise UnsafeURL("missing host")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in ALLOWED_PORTS:
        raise UnsafeURL(f"port not allowed: {port}")

    try:
        resolved = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeURL(f"cannot resolve host: {host}") from exc

    for info in resolved:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            raise UnsafeURL(f"internal address not allowed: {ip}")
    return url
