from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OCG_", case_sensitive=False)

    service_name: str = "ocg-api"
    environment: str = "dev"
    database_url: str = "postgresql+psycopg://ocg:ocg@127.0.0.1:5432/ocg"
    redis_url: str = "redis://127.0.0.1:6379/0"

    server_bind: str = "127.0.0.1"
    server_port: int = 8080
    auth_mode: str = "oidc"

    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_hs256_secret: str | None = None

    dev_auth_enabled: bool = False
    feature_raw_content: bool = False
    feature_llm_tagging: bool = False
    feature_pgvector: bool = False

    k_anonymity_k: int = Field(default=5, ge=1)
    k_anonymity_n: int = Field(default=20, ge=1)
    analytics_viewer_roles: str = "analyst,admin"

    retention_enabled: bool = True
    retention_raw_days: int = 30
    retention_trace_days: int = 180
    retention_context_days: int = 365

    jwt_clock_skew_seconds: int = 60


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
