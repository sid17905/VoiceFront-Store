"""
_playwright_worker.py — Subprocess worker for Playwright scraping.

Reads JSON from stdin, scrapes the URL, highlights the element,
extracts live DOM nodes & fresh data, outputs JSON result to stdout.
"""

from __future__ import annotations

import base64
import json
import sys
import time
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Fallback selectors per section type — try each until one matches
FALLBACK_SELECTORS = {
    "nav": ["nav", "header", "[role=navigation]", "[class*=nav]", "[class*=header]"],
    "hero": [".hero", "[class*=hero]", "header + section", "main > section:first-of-type", "section", "main"],
    "product_grid": [
        "[class*=product-grid]", "[class*=products]", "[class*=grid]",
        "[class*=menu]", "main ul", "main .grid", "[class*=card]", "[class*=product]",
    ],
    "contact": ["footer", "[class*=contact]", "[id*=contact]", "section", "main"],
}


def main() -> None:
    start_time = time.time()
    req = json.loads(sys.stdin.read())
    url = req["url"]
    selector = req["selector"]
    section_type = req.get("section_type", "nav")

    selectors_to_try = [selector]
    for fb in FALLBACK_SELECTORS.get(section_type, []):
        if fb not in selectors_to_try:
            selectors_to_try.append(fb)

    scraped_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 900},
            user_agent=USER_AGENT,
        )

        loaded = False
        try:
            page.goto(url, wait_until="networkidle", timeout=25000)
            loaded = True
        except Exception:
            try:
                page.goto(url, wait_until="load", timeout=15000)
                page.wait_for_timeout(2000)
                loaded = True
            except Exception:
                pass

        page_title = page.title() if loaded else ""

        screenshot_b64 = ""
        found = False
        matched_selector = selector
        bounding_box = {}
        css_path = ""
        computed_css = {}
        html_snippet = ""
        full_element_html = ""
        child_tags = []
        text_preview = ""
        extracted_items = []

        if loaded:
            for sel in selectors_to_try:
                exists = page.evaluate("(s) => !!document.querySelector(s)", sel)
                if exists:
                    found = True
                    matched_selector = sel

                    # Extract live child items and text
                    extracted_items = page.evaluate("""(s) => {
                        const root = document.querySelector(s);
                        if (!root) return [];
                        const items = [];
                        // Find child links, titles, prices
                        const nodes = root.querySelectorAll('a, h1, h2, h3, h4, p, span, [class*=price], [class*=title]');
                        nodes.forEach((n, idx) => {
                            const txt = (n.innerText || n.textContent || '').trim();
                            if (txt && txt.length > 2 && txt.length < 80 && items.length < 8) {
                                if (!items.some(it => it.text === txt)) {
                                    items.push({
                                        tag: n.tagName.toLowerCase(),
                                        text: txt,
                                        is_link: n.tagName === 'A' || !!n.closest('a'),
                                        href: n.getAttribute('href') || null
                                    });
                                }
                            }
                        });
                        return items;
                    }""", sel)

                    # Highlight the element on page
                    prov = page.evaluate("""(sel) => {
                        const el = document.querySelector(sel);
                        if (!el) return null;
                        el.scrollIntoView({ behavior: 'instant', block: 'center' });
                        el.style.outline = '4px solid #ff0000';
                        el.style.outlineOffset = '2px';
                        el.style.position = 'relative';
                        const label = document.createElement('div');
                        label.textContent = '>>> COMPONENT SOURCE <<<';
                        label.style.cssText = 'position:absolute;top:-28px;left:0;background:#ff0000;color:#fff;padding:4px 8px;font-size:12px;font-family:monospace;z-index:99999;white-space:nowrap;border-radius:2px;';
                        el.appendChild(label);

                        const path = [];
                        let cur = el;
                        while (cur && cur !== document.body) {
                            let tag = cur.tagName.toLowerCase();
                            if (cur.id) tag += '#' + cur.id;
                            else if (cur.className && typeof cur.className === 'string')
                                tag += '.' + cur.className.trim().split(/\\s+/).join('.');
                            path.unshift(tag);
                            cur = cur.parentElement;
                        }
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        const cssProps = ['color','background-color','font-family','font-size','font-weight','padding','margin','border-radius','display'];
                        const css = {};
                        for (const p of cssProps) css[p] = style.getPropertyValue(p);
                        return {
                            bounding_box: { top: Math.round(rect.top), left: Math.round(rect.left), width: Math.round(rect.width), height: Math.round(rect.height) },
                            css_path: ' > ' + path.join(' > '),
                            computed_css: css,
                            html_snippet: el.outerHTML.substring(0, 1000),
                            full_html: el.outerHTML.substring(0, 4000),
                            child_tags: Array.from(el.children).map(c => c.tagName.toLowerCase()),
                            text_preview: el.textContent.trim().substring(0, 300),
                        };
                    }""", sel)

                    page.wait_for_timeout(400)

                    try:
                        screenshot_bytes = page.screenshot()
                        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("ascii")
                    except Exception:
                        pass

                    if prov:
                        bounding_box = prov.get("bounding_box", {})
                        css_path = prov.get("css_path", "")
                        computed_css = prov.get("computed_css", {})
                        html_snippet = prov.get("html_snippet", "")
                        full_element_html = prov.get("full_html", "")
                        child_tags = prov.get("child_tags", [])
                        text_preview = prov.get("text_preview", "")
                    break

        browser.close()

    latency_ms = int((time.time() - start_time) * 1000)

    _output({
        "url": url,
        "selector": matched_selector,
        "found": found,
        "screenshot_b64": screenshot_b64,
        "bounding_box": bounding_box,
        "css_path": css_path,
        "computed_css": computed_css,
        "html_snippet": html_snippet,
        "full_element_html": full_element_html,
        "child_tags": child_tags,
        "text_preview": text_preview,
        "page_title": page_title,
        "scraped_at": scraped_at,
        "latency_ms": latency_ms,
        "extracted_items": extracted_items,
        "status_code": 200 if loaded else 502,
    })


def _output(data: dict) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
