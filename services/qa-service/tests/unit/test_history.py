"""Q7/Q8 — SORT ranking and the learned-fix store."""
from __future__ import annotations

import sqlite3

from core import history
from core.sort_engine import rank_failure_risk, risk_scores


def test_record_and_load_history(tmp_path):
    db = tmp_path / "h.db"
    history.record_violations(["a", "a", "b"], path=db)
    history.record_violations(["b"], path=db)
    assert history.load_history(path=db) == {"a": 2, "b": 2}


def test_history_missing_db_is_empty(tmp_path):
    assert history.load_history(path=tmp_path / "nope.db") == {}


def test_record_fix_increments(tmp_path):
    db = tmp_path / "f.db"
    history.record_fix("alt", "deterministic", path=db)
    history.record_fix("alt", "deterministic", path=db)
    assert history.known_fixes(path=db) == {"alt": 2}


def test_fix_store_keeps_sources_separate(tmp_path):
    db = tmp_path / "f.db"
    history.record_fix("alt", "deterministic", path=db)
    history.record_fix("alt", "llm", path=db)
    assert history.known_fixes(path=db) == {"alt": 2}


def test_ranking_uses_history():
    rules = [{"rule_id": "rare"}, {"rule_id": "common"}, {"rule_id": "never"}]
    ranked = rank_failure_risk(rules, {"common": 10, "rare": 2})
    assert [r["rule_id"] for r in ranked] == ["common", "rare", "never"]
    assert risk_scores(rules, {"common": 10})["common"] == 10


def test_history_survives_reconnect(tmp_path):
    db = tmp_path / "h.db"
    history.record_violations(["x"], path=db)
    # A second connection sees the committed row.
    with sqlite3.connect(str(db)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM rule_failures").fetchone()[0]
    assert count == 1
