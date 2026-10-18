from __future__ import annotations

import os
import logging
import time

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

PLACEHOLDER_KEYS = {"", "mock", "placeholder", "your_groq_api_key_here"}


class GlobalSettings(BaseSettings):
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    ASR_SERVICE_URL: str = "http://localhost:8001"
    NLP_SERVICE_URL: str = "http://localhost:8002"
    LAYOUT_SERVICE_URL: str = "http://localhost:8003"
    QA_SERVICE_URL: str = "http://localhost:8004"
    ENV: str = "dev"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "allow"

    def validate_on_startup(self, require_groq: bool = False) -> None:
        if require_groq and self.GROQ_API_KEY.strip() in PLACEHOLDER_KEYS:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Provide a valid key or set ENV=dev to use heuristic fallback."
            )
        if self.GROQ_API_KEY.strip() in PLACEHOLDER_KEYS:
            logger.warning("GROQ_API_KEY not set — heuristic/simulator fallback active.")

    @property
    def groq_mode(self) -> str:
        return "live" if self.GROQ_API_KEY.strip() not in PLACEHOLDER_KEYS else "fallback"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = GlobalSettings()
