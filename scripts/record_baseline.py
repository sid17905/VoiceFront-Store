#!/usr/bin/env python3
"""record_baseline.py — capture what actually passes today.

Writes tests/baseline.json. It records *facts*, not hopes: a suite that cannot
run because a dependency is missing is recorded as "unavailable", never "pass".

Run once before remediation (step G0), and again after each phase to see movement.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "baseline.json"

SUITES = [
    ("nlp", ROOT / "services/nlp-service", "tests"),
    ("layout", ROOT / "services/layout-service", "tests"),
    ("qa", ROOT / "services/qa-service", "tests"),
    ("publish", ROOT / "services/publish-service", "tests"),
    ("asr", ROOT / "services/asr-service", "tests"),
    ("e2e", ROOT / "tests/e2e", "."),
    ("contract", ROOT / "tests/contract", "."),
    ("layout-security", ROOT / "tests/layout", "."),
    ("security", ROOT / "tests/security", "."),
]

REQUIRED = ["pytest", "pydantic", "jinja2"]


def probe(module: str) -> bool:
    return subprocess.run([sys.executable, "-c", f"import {module}"],
                          capture_output=True).returncode == 0


def run_suite(name: str, cwd: Path, target: str) -> dict:
    if not cwd.exists():
        return {"status": "absent", "detail": f"{cwd} does not exist"}
    path = cwd / target
    if not path.exists():
        return {"status": "absent", "detail": f"{path} does not exist"}
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=str(cwd), capture_output=True, text=True, timeout=900,
    )
    out = (proc.stdout + proc.stderr).strip().splitlines()
    tail = out[-1] if out else ""
    if proc.returncode == 0:
        status = "pass"
    elif "no module named" in (proc.stdout + proc.stderr).lower():
        status = "unavailable"
    elif "no tests ran" in (proc.stdout + proc.stderr).lower():
        status = "empty"
    else:
        status = "fail"
    return {"status": status, "exit_code": proc.returncode, "summary": tail,
            "tail": out[-12:]}


def main() -> int:
    missing = [m for m in REQUIRED if not probe(m)]
    record = {
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "missing_dependencies": missing,
        "suites": {},
    }
    if missing:
        record["note"] = (
            "Baseline recorded without the full dev toolchain. Suites that need the missing "
            "modules are marked 'unavailable'; this is NOT a pass. Install "
            "`pip install -r requirements-dev.txt` inside a venv and re-run G0."
        )

    for name, cwd, target in SUITES:
        record["suites"][name] = run_suite(name, cwd, target)
        print(f"{name:16s} {record['suites'][name]['status']:12s} "
              f"{record['suites'][name].get('summary','')}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
