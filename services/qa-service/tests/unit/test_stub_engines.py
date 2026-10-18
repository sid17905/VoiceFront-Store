"""QA engine contract tests.

These replace the previous expectations that encoded the old whole-page
string-replacement behaviour ("every violation reports repaired"). The
deterministic engine deliberately reports manual rules as unfixed, so the
tests assert the properties we actually want:

  - SORT ranks by observed failure frequency.
  - A fixable rule changes the DOM and reports a deterministic source.
  - An unfixable rule is reported `manual` and never claimed as repaired.
"""
from core.detect_engine import Violation
from core.learn_engine import vectorize_rule, vectorize_rules
from core.repair_engine import repair_document, repair_violation, repair_violations
from core.sort_engine import rank_failure_risk


def test_sort_ranks_by_history():
    rules = [{"rule_id": "a"}, {"rule_id": "b"}, {"rule_id": "c"}]
    ranked = rank_failure_risk(rules, history={"c": 5, "a": 1})
    assert [r["rule_id"] for r in ranked] == ["c", "a", "b"]


def test_sort_is_stable_without_history():
    rules = [{"rule_id": "a"}, {"rule_id": "b"}, {"rule_id": "c"}]
    assert rank_failure_risk(rules) == rules


def test_fixable_rule_changes_the_dom():
    html = '<html lang="en"><body><img src="x.png"><a href="">go</a></body></html>'
    repaired, outcomes = repair_document(html, ["wcag-2.2-aa-alt-text-001"])
    assert "alt=" in repaired
    assert outcomes[0].repaired is True
    assert outcomes[0].repair_source == "deterministic"


def test_manual_rule_is_never_claimed_fixed():
    html = "<html><body><p>text</p></body></html>"
    repaired, outcomes = repair_document(html, ["wcag-2.2-aa-contrast-001"])
    assert outcomes[0].repaired is False
    assert outcomes[0].repair_source == "manual"
    assert repaired  # document is still returned intact


def test_repair_violation_legacy_wrapper():
    v = Violation(rule_id="wcag-2.2-aa-alt-text-001", severity="critical", viewport_width=375)
    result = repair_violation(v, '<html><body><img src="x"></body></html>')
    assert result.was_repaired is True
    assert result.repair_source == "deterministic"
    assert "alt=" in result.repaired_html


def test_batch_runs_per_rule():
    vs = [
        Violation(rule_id="wcag-2.2-aa-alt-text-001", severity="minor", viewport_width=320),
        Violation(rule_id="structural-empty-link-001", severity="major", viewport_width=768),
    ]
    html = '<html><body><img src="x"><a href="">go</a></body></html>'
    results = repair_violations(vs, html)
    assert all(r.repaired_html for r in results)


def test_learn_engine_is_a_noop():
    v = Violation(rule_id="a", severity="minor", viewport_width=320)
    assert vectorize_rule(v) is None
    assert vectorize_rules([v]) is None
