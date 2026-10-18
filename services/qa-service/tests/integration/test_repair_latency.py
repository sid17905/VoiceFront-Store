import time
import pytest
import sys
from pathlib import Path

qa_dir = Path(__file__).resolve().parents[3]
if str(qa_dir) not in sys.path:
    sys.path.insert(0, str(qa_dir))

def test_repair_latency_median():
    from core.repair_engine import repair_document

    html = "<html><body><img src='test.png'><a href=''></a></body></html>"
    # repair_document takes rule ids; passing Violation objects raises
    # "unhashable type" (the signature was changed in Q3).
    rule_ids = ["wcag-2.2-aa-alt-text-001", "structural-empty-link-001"]

    latencies = []
    for _ in range(10):
        start = time.monotonic()
        repaired_html, outcomes = repair_document(html, rule_ids)
        duration_ms = (time.monotonic() - start) * 1000.0
        latencies.append(duration_ms)

    latencies.sort()
    median_latency = latencies[len(latencies) // 2]
    print(f"Median repair latency: {median_latency:.2f} ms")

    assert median_latency < 500.0
    assert len(repaired_html) > 0
    assert any(o.repaired for o in outcomes)
