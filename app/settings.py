from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./clex_pharma.db"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    admin_telegram_ids: str = ""
    public_base_url: str = ""
    telegram_webhook_secret: str = ""
    process_role: str = "web"
    log_level: str = "INFO"
    default_timezone: str = "Asia/Kolkata"
    alert_score_threshold: int = Field(default=80, ge=0, le=100)
    max_http_bytes: int = Field(default=5_000_000, ge=100_000)
    http_timeout_seconds: float = Field(default=20.0, gt=0)
    crawl_interval_seconds: int = Field(default=7200, ge=60)
    digest_hour: int = Field(default=20, ge=0, le=23)
    ocr_enabled: bool = False

    @property
    def admin_ids(self) -> set[int]:
        return {
            int(value.strip())
            for value in self.admin_telegram_ids.split(",")
            if value.strip().isdigit()
        }

    @property
    def database_url_sync(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
