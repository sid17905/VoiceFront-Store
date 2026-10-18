"""SORT phase — rank rules by observed failure frequency (Q7).

Previously a pass-through whose result the router discarded. Now the ranking is
derived from persisted history (core/history.py) and returned so DETECT can be
budgeted and so the report can show that SORT did something.

Ordering rule: higher historical failure count first; ties keep the original
file order so runs are deterministic.
"""
from __future__ import annotations


def rank_failure_risk(rules: list[dict], history: dict[str, int] | None = None) -> list[dict]:
    """Return `rules` ordered by descending historical failure count.

    `history` maps rule_id -> number of observed failures. Missing rules score 0.
    Stable: equal scores preserve input order.
    """
    history = history or {}

    def score(rule: dict) -> int:
        return int(history.get(rule.get("rule_id", ""), 0))

    return sorted(rules, key=lambda r: -score(r))


def risk_scores(rules: list[dict], history: dict[str, int] | None = None) -> dict[str, int]:
    history = history or {}
    return {r.get("rule_id", ""): int(history.get(r.get("rule_id", ""), 0)) for r in rules}
