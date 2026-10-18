"""
scrape.py — POST /v1/layout/scrape

Live fetches a reference site, highlights the matched element,
returns screenshot + provenance data + fresh extracted items as JSON.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from common_utils.url_guard import UnsafeURL, assert_safe_url
except ImportError:  # pragma: no cover - local/dev fallback
    import ipaddress
    import socket
    from urllib.parse import urlparse

    class UnsafeURL(ValueError):
        pass

    def assert_safe_url(url: str) -> str:
        p = urlparse(url)
        if p.scheme not in {"http", "https"}:
            raise UnsafeURL(f"scheme not allowed: {p.scheme!r}")
        if p.username or p.password:
            raise UnsafeURL("credentials in URL are not allowed")
        host = p.hostname
        if not host:
            raise UnsafeURL("missing host")
        port = p.port or (443 if p.scheme == "https" else 80)
        if port not in {80, 443}:
            raise UnsafeURL(f"port not allowed: {port}")
        for info in socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP):
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
                raise UnsafeURL(f"internal address not allowed: {ip}")
        return url

router = APIRouter()

_SCRAPER_SCRIPT = Path(__file__).resolve().parents[1] / "_playwright_worker.py"


class ScrapeRequest(BaseModel):
    url: str
    selector: str
    section_type: str = "nav"


class ScrapeResult(BaseModel):
    url: str
    selector: str
    found: bool
    screenshot_b64: str = ""
    bounding_box: dict[str, int] = {}
    css_path: str = ""
    computed_css: dict[str, str] = {}
    html_snippet: str = ""
    full_element_html: str = ""
    child_tags: list[str] = []
    text_preview: str = ""
    page_title: str = ""
    scraped_at: str = ""
    latency_ms: int = 0
    extracted_items: list[dict[str, Any]] = []
    status_code: int = 200


@router.post("/scrape", response_model=ScrapeResult)
async def scrape_element(req: ScrapeRequest) -> ScrapeResult:
    # I-S4: never fetch a caller-supplied URL without validating it first.
    try:
        assert_safe_url(req.url)
    except UnsafeURL as exc:
        raise HTTPException(
            status_code=400,
            detail={"error_code": "SCRAPER_URL_REJECTED", "message": str(exc)},
        )

    try:
        # Off the event loop: subprocess.run blocks for up to 55s.
        result = await asyncio.to_thread(
            subprocess.run,
            [sys.executable, str(_SCRAPER_SCRIPT)],
            input=json.dumps({
                "url": req.url,
                "selector": req.selector,
                "section_type": req.section_type,
            }),
            capture_output=True,
            text=True,
            timeout=55,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=504,
            detail={
                "error_code": "SCRAPER_TIMEOUT",
                "message": "Scraping timed out after 55s",
            },
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SCRAPER_FAILED",
                "message": "Scraper failed",  # I-S6: no raw exception echo
            },
        )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SCRAPER_FAILED",
                "message": "Scraper process failed",
            },
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SCRAPER_BAD_OUTPUT",
                "message": "Scraper returned unparseable output",
            },
        )

    # I-S5: bound what a caller can pull through this endpoint.
    data["full_element_html"] = str(data.get("full_element_html", ""))[:200_000]
    data["screenshot_b64"] = str(data.get("screenshot_b64", ""))[:2_000_000]
    data["extracted_items"] = list(data.get("extracted_items", []))[:50]

    return ScrapeResult(**data)
