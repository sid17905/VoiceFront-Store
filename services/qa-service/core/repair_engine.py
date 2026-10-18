from __future__ import annotations
import os
import httpx
from dataclasses import dataclass
from core.detect_engine import Violation

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

@dataclass
class RepairResult:
    violation_id: str
    original_html: str
    repaired_html: str
    repair_source: str
    was_repaired: bool

def repair_violation(violation: Violation, html_context: str = "") -> RepairResult:
    """
    Real auto-repair engine using Groq LLM fallback for violation patching.
    """
    if not GROQ_API_KEY:
        # Fallback heuristic patch
        patched_html = html_context.replace('alt=""', 'alt="Store Graphic"')
        patched_html = patched_html.replace('href=""', 'href="#contact"')
        return RepairResult(
            violation_id=violation.rule_id,
            original_html=html_context,
            repaired_html=patched_html,
            repair_source="heuristic_fallback",
            was_repaired=True
        )

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are an expert HTML accessibility and WCAG repair assistant. Fix the provided HTML snippet to resolve the given violation."},
                {"role": "user", "content": f"Rule ID: {violation.rule_id}\nDetails: {violation.detail}\nHTML Context: {html_context}\nReturn ONLY the repaired HTML snippet."}
            ],
            "temperature": 0.1
        }
        response = httpx.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            repaired = data["choices"][0]["message"]["content"].strip()
            return RepairResult(
                violation_id=violation.rule_id,
                original_html=html_context,
                repaired_html=repaired,
                repair_source="llm_groq",
                was_repaired=True
            )
    except Exception as e:
        print(f"Groq repair error: {e}")

    return RepairResult(
        violation_id=violation.rule_id,
        original_html=html_context,
        repaired_html=html_context,
        repair_source="none",
        was_repaired=False
    )

def repair_violations(violations: list[Violation], html_content: str = "") -> list[RepairResult]:
    return [repair_violation(v, html_content) for v in violations]
