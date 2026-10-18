from core.detect_engine import Violation
from core.learn_engine import vectorize_rule, vectorize_rules
from core.repair_engine import repair_violation, repair_violations
from core.sort_engine import rank_failure_risk


def test_sort_engine_is_a_pass_through():
    rules = [{"rule_id": "a"}, {"rule_id": "b"}, {"rule_id": "c"}]
    assert rank_failure_risk(rules) == rules


def test_repair_engine_repairs_violation():
    v = Violation(rule_id="wcag-2.2-aa-contrast-001", severity="critical", viewport_width=375)
    result = repair_violation(v)
    assert result.was_repaired is True
    assert result.repair_source == "heuristic_fallback"


def test_repair_violations_batch():
    vs = [
        Violation(rule_id="a", severity="minor", viewport_width=320),
        Violation(rule_id="b", severity="major", viewport_width=768),
    ]
    result = repair_violations(vs)
    assert all(r.was_repaired is True for r in result)


def test_learn_engine_is_a_noop():
    v = Violation(rule_id="a", severity="minor", viewport_width=320)
    assert vectorize_rule(v) is None
    assert vectorize_rules([v]) is None
