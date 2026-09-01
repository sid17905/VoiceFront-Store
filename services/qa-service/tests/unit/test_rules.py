from core.detect_engine import load_rules, _CUSTOM_CHECK_JS


def test_loads_between_15_and_20_rules():
    rules = load_rules()
    assert 15 <= len(rules) <= 20


def test_every_rule_has_required_fields():
    rules = load_rules()
    for r in rules:
        assert "rule_id" in r
        assert "category" in r
        assert "check" in r
        assert "severity" in r
        assert r["severity"] in ("critical", "major", "minor")
        assert r["category"] in ("accessibility", "structural")


def test_rule_ids_are_unique():
    rules = load_rules()
    ids = [r["rule_id"] for r in rules]
    assert len(ids) == len(set(ids))


def test_axe_rules_declare_axe_rule_id():
    rules = load_rules()
    for r in rules:
        if r.get("engine") == "axe-core":
            assert "axe_rule_id" in r, f"{r['rule_id']} missing axe_rule_id"


def test_implemented_custom_checks_have_js_or_are_console_check():
    rules = load_rules()
    for r in rules:
        if r.get("engine") == "custom":
            assert (
                r["check"] in _CUSTOM_CHECK_JS
                or r["check"] == "no_console_or_page_errors"
            ), f"{r['rule_id']} has no implementation in detect_engine.py"
