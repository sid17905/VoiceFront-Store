"""
Per testing.md: unit tests use mocked I/O -- no real Whisper call, no real
Playwright render. A FakePage stands in for playwright.sync_api.Page so
_run_axe() / _run_custom_checks() can be exercised without a real browser or
a real axe-core install.

Real end-to-end rendering against the seed fixtures (fixture-good.html,
fixture-bad.html) belongs in tests/integration/ -- see test_detect_integration.py
-- since that genuinely needs Playwright's Chromium + a real axe-core build.
"""

from unittest.mock import MagicMock, patch

import core.detect_engine as detect_engine
from core.detect_engine import _run_axe, _run_custom_checks, load_rules


class FakePage:
    """Minimal stand-in for playwright.sync_api.Page."""

    def __init__(self, evaluate_fn):
        self._evaluate_fn = evaluate_fn
        self.added_scripts = []

    def add_script_tag(self, path=None, content=None):
        self.added_scripts.append(path or content)

    def evaluate(self, js, *args):
        return self._evaluate_fn(js, *args)


def test_run_axe_maps_axe_results_to_our_rule_ids(tmp_path, monkeypatch):
    rules = load_rules()

    # Pretend axe-core is installed so _run_axe doesn't short-circuit.
    fake_axe_path = tmp_path / "axe.min.js"
    fake_axe_path.write_text("/* fake axe-core */")
    monkeypatch.setattr(detect_engine, "AXE_CORE_JS_PATH", fake_axe_path)

    def fake_evaluate(js, *args):
        # Simulate axe.run() returning one real violation: color-contrast
        return {
            "violations": [
                {"id": "color-contrast", "nodes": [{}, {}]},
                {"id": "some-axe-rule-we-do-not-track", "nodes": [{}]},
            ]
        }

    page = FakePage(fake_evaluate)
    found = _run_axe(page, rules)

    assert len(found) == 1  # the untracked axe rule must be filtered out
    assert found[0]["rule_id"] == "wcag-2.2-aa-contrast-001"
    assert found[0]["severity"] == "critical"
    assert found[0]["detail"]["nodes"] == 2


def test_run_custom_checks_detects_overflow_and_console_errors():
    rules = load_rules()

    def fake_evaluate(js, *args):
        if "scrollWidth" in js:
            return True  # simulate horizontal overflow
        return False  # every other custom check passes

    page = FakePage(fake_evaluate)
    console_errors = ["TypeError: something broke"]

    found = _run_custom_checks(page, rules, console_errors)
    found_ids = {f["rule_id"] for f in found}

    assert "structural-viewport-overflow-001" in found_ids
    assert "structural-console-error-001" in found_ids
    # a check that returned False should not appear
    assert "structural-duplicate-id-001" not in found_ids


def test_run_custom_checks_clean_page_has_no_violations():
    rules = load_rules()
    page = FakePage(lambda js, *args: False)
    found = _run_custom_checks(page, rules, console_errors=[])
    assert found == []


def test_detect_violations_raises_qa_violation_error_on_playwright_crash():
    with patch("core.detect_engine.sync_playwright", side_effect=RuntimeError("boom")):
        try:
            detect_engine.detect_violations("<html></html>")
            assert False, "expected QaViolationError"
        except Exception as exc:
            assert exc.__class__.__name__ == "QaViolationError"
