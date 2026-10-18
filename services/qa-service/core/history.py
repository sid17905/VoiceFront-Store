"""Persistent QA history and learned-fix store (Q7/Q8).

SQLite via the stdlib: no server, no new dependency, and it satisfies decision
D-09. Two tables:

  rule_failures  - one row per (rule_id, observed_at); used by SORT to rank
                   rules by how often they actually fail.
  fix_store      - one row per (rule_id, source); incremented each time a
                   repair survives re-detection. This is "rule accumulation",
                   not model fine-tuning — say exactly that in the report.

The database path is configurable with QA_HISTORY_PATH and defaults to a file
next to the service. Both functions are safe to call when the DB cannot be
opened: history is an optimisation, never a hard dependency.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PATH = Path(os.getenv("QA_HISTORY_PATH", Path(__file__).resolve().parents[1] / "qa_history.db"))


def _connect(path: Path | None = None) -> sqlite3.Connection:
    target = path or DEFAULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), timeout=5)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS rule_failures ("
        " rule_id TEXT NOT NULL, observed_at TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS fix_store ("
        " rule_id TEXT NOT NULL, source TEXT NOT NULL, times_reused INTEGER NOT NULL DEFAULT 0,"
        " updated_at TEXT NOT NULL, PRIMARY KEY (rule_id, source))"
    )
    conn.commit()
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record_violations(rule_ids: list[str], path: Path | None = None) -> None:
    try:
        with _connect(path) as conn:
            conn.executemany(
                "INSERT INTO rule_failures (rule_id, observed_at) VALUES (?, ?)",
                [(rid, _now()) for rid in rule_ids],
            )
    except sqlite3.Error:
        return


def load_history(path: Path | None = None) -> dict[str, int]:
    """Return {rule_id: failure_count}. Empty dict on any error."""
    try:
        with _connect(path) as conn:
            rows = conn.execute(
                "SELECT rule_id, COUNT(*) FROM rule_failures GROUP BY rule_id"
            ).fetchall()
        return {rid: count for rid, count in rows}
    except sqlite3.Error:
        return {}


def record_fix(rule_id: str, source: str, path: Path | None = None) -> None:
    try:
        with _connect(path) as conn:
            conn.execute(
                "INSERT INTO fix_store (rule_id, source, times_reused, updated_at)"
                " VALUES (?, ?, 1, ?)"
                " ON CONFLICT(rule_id, source) DO UPDATE SET"
                " times_reused = times_reused + 1, updated_at = excluded.updated_at",
                (rule_id, source, _now()),
            )
    except sqlite3.Error:
        return


def known_fixes(path: Path | None = None) -> dict[str, int]:
    """{rule_id: total times a fix for it survived re-detection}."""
    try:
        with _connect(path) as conn:
            rows = conn.execute(
                "SELECT rule_id, SUM(times_reused) FROM fix_store GROUP BY rule_id"
            ).fetchall()
        return {rid: int(total or 0) for rid, total in rows}
    except sqlite3.Error:
        return {}
