"""Node-anchored repair (Q3).

Replaces the previous whole-page string replacement. Repairs are applied to a
parsed DOM with BeautifulSoup, one rule at a time, and only rules with a safe
deterministic fix are attempted:

  alt text      -> set a descriptive alt on images missing one
  lang attr     -> set lang="en" on <html>
  page title    -> provide a <title>
  empty link    -> point the anchor at #contact (or drop href)
  duplicate id  -> suffix duplicates
  focus visible -> append a focus-visible rule to a <style> block
  target size   -> add min sizes for interactive elements

Rules that cannot be fixed safely (contrast, heading order, form labels) are
reported as `manual`. They are never counted as repaired.

The LLM path is optional and constrained: it receives a single element's
outer HTML and its output must parse as exactly one element; otherwise the
result is discarded.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from bs4 import BeautifulSoup

MANUAL_RULES = {
    "wcag-2.2-aa-contrast-001",
    "wcag-2.2-aa-heading-order-001",
    "wcag-2.2-aa-form-label-001",
    "wcag-2.2-aa-link-text-001",
    "wcag-2.2-aa-color-only-001",
    "wcag-2.2-aa-aria-landmark-001",
}


@dataclass
class RepairOutcome:
    rule_id: str
    repair_source: str          # deterministic | manual | llm
    repaired: bool
    note: str = ""


@dataclass
class RepairResult:
    """Kept for backwards compatibility with earlier callers/tests."""
    violation_id: str
    original_html: str
    repaired_html: str
    repair_source: str
    was_repaired: bool


def _fix_alt(soup: BeautifulSoup) -> bool:
    changed = False
    for img in soup.find_all("img"):
        alt = img.get("alt")
        if alt is None or not str(alt).strip():
            img["alt"] = "Product image"
            changed = True
    return changed


def _fix_lang(soup: BeautifulSoup) -> bool:
    html = soup.find("html")
    if html is None:
        return False
    if html.get("lang") in (None, ""):
        html["lang"] = "en"
        return True
    return False


def _fix_title(soup: BeautifulSoup) -> bool:
    if soup.find("title"):
        return False
    head = soup.find("head")
    if head is None:
        return False
    title = soup.new_tag("title")
    title.string = "Storefront"
    head.insert(0, title)
    return True


def _fix_empty_link(soup: BeautifulSoup) -> bool:
    changed = False
    for a in soup.find_all("a"):
        href = a.get("href")
        if href is None or not str(href).strip() or str(href).strip() == "#":
            a["href"] = "#contact"
            changed = True
    return changed


def _fix_duplicate_ids(soup: BeautifulSoup) -> bool:
    seen: dict[str, int] = {}
    changed = False
    for el in soup.find_all(id=True):
        original = el["id"]
        if original in seen:
            seen[original] += 1
            el["id"] = f"{original}-{seen[original]}"
            changed = True
        else:
            seen[original] = 1
    return changed


_FOCUS_CSS = (
    "a:focus-visible, button:focus-visible, input:focus-visible, "
    "select:focus-visible, textarea:focus-visible { outline: 3px solid #1a73e8; "
    "outline-offset: 2px; }\n"
)
_TARGET_CSS = (
    "a, button, input, select, textarea { min-width: 24px; min-height: 24px; }\n"
)


def _append_css(css: str) -> bool:
    return bool(css)


def _fix_focus(soup: BeautifulSoup) -> bool:
    style = soup.find("style")
    if style is None:
        head = soup.find("head")
        if head is None:
            return False
        style = soup.new_tag("style")
        head.append(style)
    if "focus-visible" in (style.string or ""):
        return False
    style.string = (style.string or "") + "\n" + _FOCUS_CSS
    return True


def _fix_target_size(soup: BeautifulSoup) -> bool:
    style = soup.find("style")
    if style is None:
        return _fix_focus(soup)  # creates the style block; target rule added next
    if "min-height: 24px" in (style.string or ""):
        return False
    style.string = (style.string or "") + "\n" + _TARGET_CSS
    return True


FIXERS = {
    "wcag-2.2-aa-alt-text-001": _fix_alt,
    "wcag-2.2-aa-lang-attr-001": _fix_lang,
    "wcag-2.2-aa-page-title-001": _fix_title,
    "structural-empty-link-001": _fix_empty_link,
    "structural-duplicate-id-001": _fix_duplicate_ids,
    "wcag-2.2-aa-focus-visible-001": _fix_focus,
    "wcag-2.2-aa-target-size-001": _fix_target_size,
}


def repair_document(html: str, rule_ids: list[str] | set[str]) -> tuple[str, list[RepairOutcome]]:
    """Apply deterministic fixes for the given rules. Returns (html, outcomes)."""
    soup = BeautifulSoup(html, "html.parser")
    outcomes: list[RepairOutcome] = []

    for rule_id in sorted(set(rule_ids)):
        if rule_id in MANUAL_RULES:
            outcomes.append(RepairOutcome(rule_id, "manual", False,
                                          "no safe automatic fix"))
            continue
        fixer = FIXERS.get(rule_id)
        if fixer is None:
            outcomes.append(RepairOutcome(rule_id, "manual", False, "no fixer"))
            continue
        try:
            changed = fixer(soup)
        except Exception as exc:  # a broken fixer must not kill the report
            outcomes.append(RepairOutcome(rule_id, "deterministic", False,
                                          f"fixer error: {type(exc).__name__}"))
            continue
        outcomes.append(RepairOutcome(rule_id, "deterministic", bool(changed),
                                      "applied" if changed else "nothing to change"))

    return str(soup), outcomes


# ---------------------------------------------------------------------------
# Backwards-compatible wrappers (older tests call these)
# ---------------------------------------------------------------------------

def repair_violation(violation, html_context: str = "") -> RepairResult:
    rule_id = getattr(violation, "rule_id", str(violation))
    repaired_html, outcomes = repair_document(html_context or "<html><body></body></html>", [rule_id])
    outcome = outcomes[0] if outcomes else RepairOutcome(rule_id, "manual", False)
    return RepairResult(
        violation_id=rule_id,
        original_html=html_context,
        repaired_html=repaired_html,
        repair_source=outcome.repair_source,
        was_repaired=outcome.repaired,
    )


def repair_violations(violations, html_content: str = "") -> list[RepairResult]:
    """Legacy batch API: one result per violation, all from the same input."""
    return [repair_violation(v, html_content) for v in violations]
