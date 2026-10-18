from __future__ import annotations

from routers.publish import router as publish_router
from common_utils.security import SecurityMiddleware
from common_utils.service_app import create_app

app = create_app("publish-service", "0.1.0")
app.add_middleware(SecurityMiddleware)
app.include_router(publish_router)
