from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    debug: bool = False
    app_host: str = "0.0.0.0"
    app_port: int = 8080
    app_public_url: str = "http://localhost:8080"
    webapp_url: str = "http://localhost:3000"

    bot_token: str = ""
    bot_username: str = "proofbot_demo_bot"
    bot_mode: str = "polling"
    webhook_base_url: str = ""
    webhook_secret_token: str = "change-me"

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "proofbot"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/proofbot"
    redis_url: str = "redis://redis:6379/0"

    polza_api_key: str = ""
    polza_base_url: str = "https://polza.ai/api/v1"
    polza_model: str = "gpt-4.1-mini"
    polza_fallback_model: str = "gpt-4.1-mini"
    polza_timeout_seconds: float = 45.0
    polza_max_retries: int = 3

    free_requests_initial: int = 10
    referral_bonus_inviter: int = 2
    referral_bonus_invitee: int = 1
    max_active_analyses_per_user: int = 1
    max_ai_concurrency: int = 20

    admin_tg_ids: str = ""
    pay_support_text: str = "По вопросам оплаты напишите @support_username"
    pdf_storage_path: str = str(BASE_DIR / "storage" / "pdf")
    log_level: str = "INFO"
    sentry_dsn: str | None = None

    rate_limit_messages_per_minute: int = 10
    rate_limit_api_per_minute: int = 60
    telegram_login_max_age_seconds: int = 86400
    prompt_version: str = "v1"
    stars_provider_token: str = ""
    payment_callback_url: str = ""
    broadcast_throttle_per_second: float = 20.0

    @property
    def admin_ids(self) -> set[int]:
        raw = [value.strip() for value in self.admin_tg_ids.split(",") if value.strip()]
        return {int(value) for value in raw}

    @field_validator("bot_mode")
    @classmethod
    def validate_bot_mode(cls, value: str) -> str:
        allowed = {"polling", "webhook", "disabled"}
        if value not in allowed:
            raise ValueError(f"bot_mode must be one of {allowed}")
        return value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    Path(settings.pdf_storage_path).mkdir(parents=True, exist_ok=True)
    return settings

