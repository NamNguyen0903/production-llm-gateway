from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]
ProviderName = Literal["openai", "gemini"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Production LLM Gateway"
    app_version: str = "0.1.0"
    environment: Environment = "local"
    debug: bool = False
    log_level: LogLevel = "INFO"

    api_v1_prefix: str = "/v1"
    request_id_header: str = "X-Request-ID"

    database_url: str = "postgresql+asyncpg://gateway:gateway@localhost:5432/llm_gateway"
    redis_url: str = "redis://localhost:6379/0"

    primary_llm_provider: ProviderName = "openai"
    fallback_llm_provider: ProviderName = "gemini"

    openai_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
    api_key_hmac_secret: SecretStr | None = None

    llm_attempt_timeout_seconds: float = Field(
        default=10.0,
        gt=0,
        le=60,
    )
    llm_total_timeout_seconds: float = Field(
        default=25.0,
        gt=0,
        le=120,
    )
    llm_max_retries: int = Field(
        default=1,
        ge=0,
        le=3,
    )
    llm_backoff_base_seconds: float = Field(
        default=0.5,
        ge=0,
        le=10,
    )

    cache_ttl_seconds: int = Field(
        default=600,
        ge=1,
        le=86400,
    )
    rate_limit_requests: int = Field(
        default=30,
        ge=1,
    )
    rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
    )

    @model_validator(mode="after")
    def validate_provider_configuration(self) -> Self:
        if self.primary_llm_provider == self.fallback_llm_provider:
            raise ValueError("Primary and fallback LLM providers must be different.")

        if self.llm_total_timeout_seconds <= self.llm_attempt_timeout_seconds:
            raise ValueError("Total LLM timeout must be greater than attempt timeout.")

        return self


@lru_cache
def get_settings() -> Settings:
    """Return one cached Settings instance per application process."""

    return Settings()
