from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Trade Opportunities API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = "gemini-2.5-flash"

    api_key: str = Field(default="change-me-in-production", alias="TRADE_API_KEY")
    guest_access_enabled: bool = True
    auth_header_name: str = "X-API-Key"

    session_secret_key: str = Field(default="replace-this-secret-in-production", alias="SESSION_SECRET_KEY")
    session_max_age_seconds: int = 60 * 60 * 12

    rate_limit_requests: int = 10
    rate_limit_window_seconds: int = 60

    request_timeout_seconds: int = 15
    max_sector_length: int = 40
    max_search_results: int = 8
    max_source_chars: int = 7000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
