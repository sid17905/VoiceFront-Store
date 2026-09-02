"""
scrape.py — POST /v1/layout/scrape

Live fetches a reference site, highlights the matched element,
returns screenshot + provenance data + fresh extracted items as JSON.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
    try:
        result = subprocess.run(
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
                "message": f"Scraping {req.url} timed out after 55s",
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SCRAPER_FAILED",
                "message": str(exc),
            },
        )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SCRAPER_FAILED",
                "message": result.stderr[:500] if result.stderr else "Unknown error",
            },
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "SCRAPER_BAD_OUTPUT",
                "message": result.stdout[:500] if result.stdout else "Empty output",
            },
        )

    return ScrapeResult(**data)
