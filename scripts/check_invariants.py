#!/usr/bin/env python3
"""check_invariants.py — static checks that fail loudly.

Each rule inspects the tree and exits non-zero on violation, printing file:line.
These are deliberately simple and dependency-free so they run anywhere.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "build",
             ".dart_tool", ".pytest_cache", "scrapy", "temp_fresh", ".idea"}

PY = "*.py"


def walk(pattern: str = PY):
    for p in ROOT.rglob(pattern):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file():
            yield p


def grep(pattern: str, pattern_glob: str = PY, exclude: tuple[str, ...] = ()) -> list[str]:
    rx = re.compile(pattern)
    hits = []
    for p in walk(pattern_glob):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if any(rel.startswith(e) for e in exclude):
            continue
        try:
            for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if rx.search(line):
                    hits.append(f"{rel}:{i}: {line.strip()[:160]}")
        except OSError:
            continue
    return hits


def report(name: str, hits: list[str], allow: int = 0) -> int:
    if len(hits) <= allow:
        print(f"PASS {name} ({len(hits)} hits, allowed {allow})")
        return 0
    print(f"FAIL {name} — {len(hits)} hits (allowed {allow})")
    for h in hits[:60]:
        print("  " + h)
    return 1


RULES = {}


def rule(name):
    def deco(fn):
        RULES[name] = fn
        return fn
    return deco


@rule("I-A5")
def no_direct_groq():
    hits = grep(r"api\.groq\.com") + grep(r"Groq\(api_key")
    hits = [h for h in hits if "common_utils/groq_client.py" not in h and "/test" not in h]
    return report("no direct Groq access", hits)


@rule("I-A2S")
def service_factory():
    """Each service main.py should construct via create_app once A2 lands."""
    problems = []
    for svc in ("asr-service", "nlp-service", "layout-service", "qa-service", "publish-service"):
        main = ROOT / "services" / svc / "main.py"
        if not main.exists():
            problems.append(f"{svc}: main.py missing")
            continue
        text = main.read_text(encoding="utf-8", errors="ignore")
        if "create_app(" not in text:
            problems.append(f"services/{svc}/main.py: does not use create_app()")
    return report("shared service factory", problems)


@rule("schema-drift")
def schema_drift():
    """Compare Pydantic model_json_schema with the committed JSON Schema."""
    try:
        sys.path.insert(0, str(ROOT / "packages"))
        from schemas.entity_types import StorefrontSpec  # type: ignore
    except Exception as exc:  # pydantic missing etc.
        print(f"SKIP schema-drift (cannot import: {type(exc).__name__})")
        return 0
    import json
    committed = ROOT / "packages/schemas/storefront_spec.schema.json"
    if not committed.exists():
        return report("schema drift", ["storefront_spec.schema.json missing"])
    want = StorefrontSpec.model_json_schema()
    have = json.loads(committed.read_text(encoding="utf-8"))
    if want != have:
        return report("schema drift", ["packages/schemas/storefront_spec.schema.json is out of date; run scripts/gen_schemas.py"])
    print("PASS schema drift")
    return 0


@rule("no-syspath")
def no_syspath():
    hits = grep(r"sys\.path\.(insert|append)")
    # The checker itself, and the scripts that legitimately bootstrap before a
    # package install exists, are exempt until A4 removes the need entirely.
    exempt = ("scripts/check_invariants.py", "scripts/record_baseline.py",
              "scripts/generate_music_store.py", "scripts/test_storefront_generator.py")
    hits = [h for h in hits if not any(h.startswith(e) for e in exempt)]
    return report("no sys.path hacks", hits)


@rule("qa-httpx")
def qa_httpx():
    req = ROOT / "services/qa-service/requirements.txt"
    if not req.exists():
        return report("qa httpx", ["requirements.txt missing"])
    text = req.read_text(encoding="utf-8")
    uses = bool(grep(r"^import httpx|^\s+import httpx", "*.py"))
    if uses and "httpx" not in text:
        return report("qa httpx", ["repair_engine imports httpx but requirements.txt lacks it"])
    print("PASS qa httpx")
    return 0


@rule("template-page")
def template_page():
    problems = []
    for t in sorted((ROOT / "services/layout-service/templates").glob("*.jinja2")):
        if t.name.startswith("_"):
            continue
        text = t.read_text(encoding="utf-8", errors="ignore")
        if 'lang="en"' not in text:
            problems.append(f"{t.name}: missing lang=\"en\"")
        if "raw_text" in text:
            problems.append(f"{t.name}: uses removed field location.raw_text")
        if "format(product.price)" in text:
            problems.append(f"{t.name}: numeric price formatting will crash on None")
        if 'name="description"' not in text:
            problems.append(f"{t.name}: missing meta description")
    return report("template page correctness", problems)


@rule("testpaths")
def testpaths():
    ini = ROOT / "pytest.ini"
    text = ini.read_text(encoding="utf-8") if ini.exists() else ""
    if "testpaths" not in text:
        return report("pytest testpaths", ["pytest.ini has no testpaths — root pytest will walk scrapy/ and .venv/"])
    print("PASS pytest testpaths")
    return 0


@rule("secrets")
def secrets():
    hits = grep(r"gsk_[A-Za-z0-9]{20,}|sk_omniroute|super-secret-iron-man")
    hits = [h for h in hits if not h.startswith("scripts/check_invariants.py")]
    return report("no secrets in tracked source", hits)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", choices=sorted(RULES) + ["all"], default="all")
    args = ap.parse_args()
    names = sorted(RULES) if args.rule == "all" else [args.rule]
    worst = 0
    for n in names:
        worst |= RULES[n]()
    return worst


if __name__ == "__main__":
    sys.exit(main())
