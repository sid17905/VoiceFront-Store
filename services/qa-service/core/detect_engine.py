"""
services/qa-service/core/detect_engine.py

L5 DETECT phase (Architect.md). Phase 1 scope per person_d_qa_publish.md:
"a minimal detect_engine.py that runs your 15-20 rules against a rendered page and
returns a violation list -- no auto-repair yet." repair_engine.py / learn_engine.py
are separate, stubbed modules (Phase 3-4 real logic).

Renders the bundle at every configured viewport width (QA_VIEWPORT_WIDTHS,
environment.md: 320,375,768,1024,1440) via Playwright, and checks it against the
constraint rules in data/constraint-rules/*.json using two engines:
  - "axe-core": delegated to the real axe-core JS library, injected into the page.
  - "custom":   hand-written JS checks executed via page.evaluate(), for rules
                axe-core doesn't cover (viewport overflow, broken img src, console
                errors, duplicate ids, etc. -- see data.md).

Naming follows common_references.md: detect_violations() -> JSON field "violations".
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

# Import shared exception base (packages/common-utils/exceptions.py)
try:
    from common_utils.exceptions import QaViolationError
except ImportError:  # pragma: no cover - fallback for standalone/local testing
    class QaViolationError(Exception):
        def __init__(self, error_code: str, message: str):
            self.error_code = error_code
            self.message = message
            super().__init__(f"{error_code}: {message}")


DEFAULT_RULES_DIR = Path(__file__).resolve().parents[3] / "data" / "constraint-rules"
DEFAULT_VIEWPORT_WIDTHS = [320, 375, 768, 1024, 1440]  # QA_VIEWPORT_WIDTHS, environment.md
VIEWPORT_HEIGHT = 900  # arbitrary but consistent tall viewport; width is what the rules care about

# axe-core is expected to be installed via `npm install axe-core` (per files.md's
# node_modules convention) so the raw JS can be injected into the Playwright page
# without a network call at render time -- keeps DETECT fast and offline-safe.
AXE_CORE_JS_PATH = (
    Path(__file__).resolve().parents[1] / "node_modules" / "axe-core" / "axe.min.js"
)


@dataclass
class Violation:
    rule_id: str
    severity: str
    viewport_width: int
    was_repaired: bool = False
    repair_source: str | None = None
    # Extra debug context -- not part of the wire contract in api_contracts.md,
    # strip these before serializing the API response, but useful for
    # sort_engine.py / repair_engine.py in later phases.
    detail: dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self) -> dict:
        """Shape matches qa_violations in api_contracts.md / data.md exactly."""
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "viewport_width": self.viewport_width,
            "was_repaired": self.was_repaired,
            "repair_source": self.repair_source,
        }


def load_rules(rules_dir: str | Path = DEFAULT_RULES_DIR) -> list[dict]:
    """Load every *.json constraint rule from data/constraint-rules/."""
    rules_dir = Path(rules_dir)
    rules = []
    for rule_file in sorted(rules_dir.glob("*.json")):
        with open(rule_file, encoding="utf-8") as f:
            rules.append(json.load(f))
    if not rules:
        raise QaViolationError(
            "QA_NO_RULES_LOADED", f"No constraint rules found in {rules_dir}"
        )
    return rules


# ---------------------------------------------------------------------------
# axe-core rules
# ---------------------------------------------------------------------------

_AXE_SEVERITY_BY_RULE: dict[str, tuple[str, str]] = {}  # axe_rule_id -> (rule_id, severity)


def _index_axe_rules(rules: list[dict]) -> dict[str, tuple[str, str]]:
    return {
        r["axe_rule_id"]: (r["rule_id"], r["severity"])
        for r in rules
        if r.get("engine") == "axe-core"
    }


def _run_axe(page, rules: list[dict]) -> list[dict]:
    """Inject axe-core and run it, restricted to the axe rule IDs this project
    actually maps to a constraint rule (so a random axe rule we haven't reviewed
    doesn't silently become a "violation" no one signed off on)."""
    if not AXE_CORE_JS_PATH.exists():
        raise QaViolationError(
            "QA_AXE_CORE_MISSING",
            f"axe-core not found at {AXE_CORE_JS_PATH} -- run `npm install axe-core` "
            "in services/qa-service/ first.",
        )
    axe_index = _index_axe_rules(rules)
    axe_rule_ids = list(axe_index.keys())

    page.add_script_tag(path=str(AXE_CORE_JS_PATH))
    axe_results = page.evaluate(
        """(ruleIds) => axe.run(document, { runOnly: { type: 'rule', values: ruleIds } })""",
        axe_rule_ids,
    )

    found = []
    for v in axe_results.get("violations", []):
        mapped = axe_index.get(v["id"])
        if not mapped:
            continue  # not one of our reviewed rules -- ignore
        rule_id, severity = mapped
        found.append(
            {
                "rule_id": rule_id,
                "severity": severity,
                "detail": {"axe_rule_id": v["id"], "nodes": len(v.get("nodes", []))},
            }
        )
    return found


# ---------------------------------------------------------------------------
# Custom (non-axe) checks -- each returns True if a VIOLATION was found
# ---------------------------------------------------------------------------

_CUSTOM_CHECK_JS = {
    "no_horizontal_overflow": """
        () => document.documentElement.scrollWidth > window.innerWidth + 1
    """,
    "no_broken_image_src": """
        () => Array.from(document.images).some(img => img.complete && img.naturalWidth === 0)
    """,
    "no_duplicate_ids": """
        () => {
            const ids = Array.from(document.querySelectorAll('[id]')).map(e => e.id);
            return new Set(ids).size !== ids.length;
        }
    """,
    "no_empty_links": """
        () => Array.from(document.querySelectorAll('a')).some(a =>
            (!a.getAttribute('href') || a.getAttribute('href').trim() === '') ||
            (a.textContent.trim() === '' && !a.querySelector('img[alt]'))
        )
    """,
    "viewport_meta_present": """
        () => !document.querySelector('meta[name="viewport"]')
    """,
    "focus_indicator_not_removed": """
        () => Array.from(document.querySelectorAll('a, button, input, select, textarea')).some(el => {
            const style = window.getComputedStyle(el, ':focus');
            return style.outlineStyle === 'none' && style.boxShadow === 'none';
        })
    """,
    "tap_target_min_size": """
        (minPx) => Array.from(document.querySelectorAll('a, button, input, select')).some(el => {
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0 && (r.width < minPx || r.height < minPx);
        })
    """,
}


def _run_custom_checks(page, rules: list[dict], console_errors: list[str]) -> list[dict]:
    found = []
    for rule in rules:
        if rule.get("engine") != "custom":
            continue
        check = rule["check"]

        if check == "no_console_or_page_errors":
            if console_errors:
                found.append(
                    {
                        "rule_id": rule["rule_id"],
                        "severity": rule["severity"],
                        "detail": {"errors": console_errors[:5]},
                    }
                )
            continue

        js = _CUSTOM_CHECK_JS.get(check)
        if js is None:
            continue  # not implemented yet -- fine for MVP, expand as rules grow toward 50

        if check == "tap_target_min_size":
            threshold = rule.get("threshold_px", 24)
            is_violation = page.evaluate(js, threshold)
        else:
            is_violation = page.evaluate(js)

        if is_violation:
            found.append({"rule_id": rule["rule_id"], "severity": rule["severity"], "detail": {}})
    return found


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def detect_violations(
    html_content: str,
    viewport_widths: list[int] | None = None,
    rules_dir: str | Path = DEFAULT_RULES_DIR,
) -> list[Violation]:
    """
    Render `html_content` at each viewport width and check it against every
    constraint rule in `rules_dir`. Returns a flat list of Violation objects
    (one per rule x viewport where it failed -- the same rule can legitimately
    fail at one width and pass at another, e.g. viewport overflow).

    No SORT ranking and no REPAIR attempt here -- see sort_engine.py /
    repair_engine.py. This function only detects.
    """
    viewport_widths = viewport_widths or DEFAULT_VIEWPORT_WIDTHS
    rules = load_rules(rules_dir)
    all_violations: list[Violation] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                for width in viewport_widths:
                    page = browser.new_page(viewport={"width": width, "height": VIEWPORT_HEIGHT})
                    console_errors: list[str] = []
                    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
                    page.on("pageerror", lambda exc: console_errors.append(str(exc)))

                    page.set_content(html_content, wait_until="load")

                    axe_hits = _run_axe(page, rules)
                    custom_hits = _run_custom_checks(page, rules, console_errors)

                    for hit in axe_hits + custom_hits:
                        all_violations.append(
                            Violation(
                                rule_id=hit["rule_id"],
                                severity=hit["severity"],
                                viewport_width=width,
                                detail=hit.get("detail", {}),
                            )
                        )
                    page.close()
            finally:
                browser.close()
    except QaViolationError:
        raise
    except Exception as exc:  # Playwright crash, browser not installed, etc.
        raise QaViolationError("QA_DETECT_PIPELINE_FAILURE", str(exc)) from exc

    return all_violations


if __name__ == "__main__":
    # Quick manual smoke test against a static fixture, e.g.:
    #   python core/detect_engine.py path/to/fixture.html
    import sys

    fixture_path = sys.argv[1] if len(sys.argv) > 1 else None
    if not fixture_path:
        print("Usage: python detect_engine.py <path-to-html-fixture>")
        raise SystemExit(1)

    html = Path(fixture_path).read_text(encoding="utf-8")
    violations = detect_violations(html)
    print(f"Found {len(violations)} violations:")
    for v in violations:
        print(f"  [{v.severity:8s}] {v.rule_id} @ {v.viewport_width}px  {v.detail}")
