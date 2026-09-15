"""Centralized application configuration.

Every tunable value in the application is declared here and loaded from
environment variables (or a local `.env` file). Nothing else in the codebase
reads `os.environ` directly - that is what keeps configuration auditable and
secrets out of the source tree.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -------------------------------------------------------
    app_name: str = "Hirelens"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # --- Logging -----------------------------------------------------------
    log_level: str = "INFO"
    log_json: bool = False

    # --- CORS --------------------------------------------------------------
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # --- Uploads -----------------------------------------------------------
    max_upload_mb: int = 10
    allowed_upload_extensions: str = ".pdf,.docx,.txt"

    # --- AI ----------------------------------------------------------------
    # "anthropic" - paid, prepaid credit required
    # "gemini"    - has a free tier, good for running this project at no cost
    # "null"      - AI disabled; upload and parsing still work
    ai_provider: Literal["anthropic", "gemini", "null"] = "anthropic"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    ai_max_tokens: int = 4000
    ai_timeout_seconds: int = 90
    ai_max_retries: int = 2
    ai_cache_enabled: bool = True

    # --- Database (Phase 4) ------------------------------------------------
    database_url: str = ""

    # --- Derived helpers ---------------------------------------------------
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_extensions(self) -> set[str]:
        return {
            e.strip().lower()
            for e in self.allowed_upload_extensions.split(",")
            if e.strip()
        }

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def ai_api_key(self) -> str:
        """The key belonging to the selected provider."""
        if self.ai_provider == "anthropic":
            return self.anthropic_api_key.strip()
        if self.ai_provider == "gemini":
            return self.gemini_api_key.strip()
        return ""

    @property
    def ai_model(self) -> str:
        if self.ai_provider == "anthropic":
            return self.anthropic_model
        if self.ai_provider == "gemini":
            return self.gemini_model
        return ""

    @property
    def ai_enabled(self) -> bool:
        """True only when a usable provider AND its credentials are configured."""
        if self.ai_provider == "null":
            return False
        return bool(self.ai_api_key)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached accessor. FastAPI dependencies use this so a single Settings
    instance is shared for the process lifetime."""
    return Settings()
