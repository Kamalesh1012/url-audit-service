"""Centralized, env-driven configuration. Defaults are dev-safe."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "URL Audit Service"
    environment: str = "development"

    fetch_timeout_seconds: float = 8.0
    max_concurrent_audits: int = 10
    max_redirects: int = 5

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    rate_limit: str = "30/minute"

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "AUDIT_"


settings = Settings()
