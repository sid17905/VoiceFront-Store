import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SERVICE_ROOT.parents[1]

for p in (SERVICE_ROOT, REPO_ROOT / "packages"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
