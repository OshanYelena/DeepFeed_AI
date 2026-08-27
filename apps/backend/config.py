"""
DeepFeed AI - Application Configuration
Loads all settings from environment variables.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "DeepFeed AI"
    app_env: str = "local"
    app_debug: bool = False
    app_secret_key: str = "change-me"

    # Database
    database_url: str = "postgresql+asyncpg://deepfeed:deepfeed@localhost:5432/deepfeed"
    database_sync_url: str = "postgresql://deepfeed:deepfeed@localhost:5432/deepfeed"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Queue
    rabbitmq_url: str = "amqp://deepfeed:deepfeed@localhost:5672/"
    celery_broker_url: str = "amqp://deepfeed:deepfeed@localhost:5672/"
    celery_result_backend: str = "rpc://"

    # JWT
    jwt_secret_key: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    default_llm_provider: str = "anthropic"

    # Observability
    otel_service_name: str = "deepfeed-backend"
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Content Processing
    max_content_length_bytes: int = 10_485_760
    extraction_timeout_seconds: int = 30

    # Agentic
    adaptation_schedule_cron: str = "0 2 * * *"
    reflection_schedule_cron: str = "0 3 * * *"

    # Manual discovery (on-demand "Discover Now" button)
    # 10/day matches the cron of every hour, but lets impatient users burst.
    discovery_manual_daily_limit: int = 10
    # Seconds between two clicks by the same user. Stops accidental double-clicks
    # from spawning duplicate runs while still letting users retry within a session.
    discovery_manual_cooldown_seconds: int = 60
    # Cron expression for scheduled discovery — used by the status endpoint to
    # compute "next automatic run." Keep in sync with celery beat_schedule.
    discovery_schedule_cron: str = "0 * * * *"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
