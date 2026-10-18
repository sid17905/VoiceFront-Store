#!/usr/bin/env python3
"""verify_step.py — run a step's proof and report GREEN / RED / SKIP honestly.

Usage:
    python scripts/verify_step.py --list
    python scripts/verify_step.py S1
    python scripts/verify_step.py --all

Exit codes: 0 = green (or skipped), 1 = red, 2 = unknown step.
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOFS = ROOT / "docs" / "proofs.json"
STATE = ROOT / "docs" / "state.json"

GREEN, RED, SKIP = "\033[32mGREEN\033[0m", "\033[31mRED\033[0m", "\033[33mSKIP\033[0m"


def load() -> dict:
    return json.loads(PROOFS.read_text(encoding="utf-8"))["steps"]


def save_state(step: str, status: str, output: str) -> None:
    state = {}
    if STATE.exists():
        try:
            state = json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            state = {}
    state[step] = {"status": status, "proof": output.strip()[-1200:],
                   "at": subprocess.run(["python", "-c", "import datetime;print(datetime.datetime.now().isoformat(timespec='seconds'))"],
                                        capture_output=True, text=True).stdout.strip()}
    STATE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=1800)


def verify(step: str, spec: dict) -> int:
    title = spec.get("title", "")
    print(f"\n=== {step} — {title}")

    skip_if = spec.get("skip_if")
    if skip_if:
        probe = run(skip_if)
        if probe.returncode != 0:
            print(f"  {SKIP} prerequisite missing: {' '.join(shlex.quote(c) for c in skip_if)}")
            print(f"  reason: {(probe.stderr or probe.stdout).strip().splitlines()[-1] if (probe.stderr or probe.stdout).strip() else 'no output'}")
            save_state(step, "skip", "prerequisite missing")
            return 0

    cmd = spec["cmd"]
    print(f"  $ {' '.join(shlex.quote(c) for c in cmd)}")
    proc = run(cmd)
    tail = (proc.stdout or "") + (proc.stderr or "")
    print("\n".join("  " + line for line in tail.strip().splitlines()[-15:]))
    if proc.returncode == 0:
        print(f"  {GREEN}")
        save_state(step, "green", tail)
        return 0
    print(f"  {RED} (exit {proc.returncode})")
    save_state(step, "red", tail)
    return 1


def git_clean() -> int:
    out = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    if out.strip():
        print("  working tree is not clean:")
        print("\n".join("  " + l for l in out.strip().splitlines()[:40]))
        return 1
    print("  working tree clean")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--git-clean", action="store_true")
    args = ap.parse_args()

    if args.git_clean:
        return git_clean()

    steps = load()
    if args.list:
        for key, spec in steps.items():
            print(f"{key:5s} {spec.get('title','')}")
        return 0
    if args.all:
        results = {k: verify(k, v) for k, v in steps.items()}
        print("\nsummary:", {k: ("green" if v == 0 else "red") for k, v in results.items()})
        return 0 if all(v == 0 for v in results.values()) else 1
    if not args.step:
        ap.print_help()
        return 2
    if args.step not in steps:
        print(f"unknown step {args.step}; run --list")
        return 2
    return verify(args.step, steps[args.step])


if __name__ == "__main__":
    sys.exit(main())
