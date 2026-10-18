#!/usr/bin/env python3
"""Run every test suite in its own process.

Each service defines a top-level package named `core` (and several define
`routers`), so collecting them in one pytest process makes the first-imported
`core` win and the rest fail with ModuleNotFoundError. That collision is the
reason step A4 exists.

Until A4 lands, this runner is the honest way to execute the full suite: one
subprocess per suite, real exit codes, no shared module cache.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUITES = [
    ("tests/layout", ROOT, ["tests/layout"]),
    ("tests/security", ROOT, ["tests/security"]),
    ("tests/e2e", ROOT, ["tests/e2e"]),
    ("tests/contract", ROOT, ["tests/contract"]),
    ("tests/eval", ROOT, ["tests/eval"]),
    ("services/asr-service", ROOT / "services/asr-service", ["tests"]),
    ("services/nlp-service", ROOT / "services/nlp-service", ["tests"]),
    ("services/layout-service", ROOT / "services/layout-service", ["tests"]),
    ("services/qa-service", ROOT / "services/qa-service", ["tests"]),
    ("services/publish-service", ROOT / "services/publish-service", ["tests"]),
]


def main() -> int:
    failures = []
    for name, cwd, requested in SUITES:
        targets = [t for t in requested if (cwd / t).exists()]
        if not targets:
            print(f"{name:32s} SKIP (no test targets)")
            continue
        test_files = [p for t in targets for p in (cwd / t).rglob("test_*.py")]
        if not test_files:
            print(f"{name:32s} SKIP (no test_*.py; T6 has not produced assertions yet)")
            continue
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", *targets, "-q", "--no-header",
             "-p", "no:cacheprovider"],
            cwd=str(cwd), capture_output=True, text=True, timeout=1800,
        )
        tail = (proc.stdout + proc.stderr).strip().splitlines()
        summary = tail[-1] if tail else ""
        status = "PASS" if proc.returncode == 0 else "FAIL"
        print(f"{name:32s} {status:4s} {summary}")
        if proc.returncode != 0:
            failures.append((name, tail[-25:]))

    if failures:
        print("\n--- failure detail ---")
        for name, lines in failures:
            print(f"\n[{name}]")
            print("\n".join(lines))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
