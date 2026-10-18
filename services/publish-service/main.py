from __future__ import annotations

import sys
from pathlib import Path

# Make `common_utils` importable when the service is run directly from its own
# directory (the container sets WORKDIR to the service). Step A4 replaces this
# with installed packages.
_packages = Path(__file__).resolve().parents[2] / "packages"
if str(_packages) not in sys.path:
    sys.path.insert(0, str(_packages))

from routers.publish import router as publish_router
from common_utils.security import SecurityMiddleware
from common_utils.service_app import create_app

app = create_app("publish-service", "0.1.0")
app.add_middleware(SecurityMiddleware)
app.include_router(publish_router)
