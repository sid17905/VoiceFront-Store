import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = SERVICE_ROOT.parents[1]

sys.path.insert(0, str(SERVICE_ROOT))
sys.path.insert(0, str(REPO_ROOT / "packages"))
sys.path.insert(0, str(REPO_ROOT))

if "core" in sys.modules:
    del sys.modules["core"]
