from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Java Masters Exam Engine"
    api_prefix: str = "/api/v1"
    database_url: str
    admin_jwt_secret: str
    admin_jwt_algorithm: str = "HS256"
    admin_jwt_expire_minutes: int = 60
    allowed_origins: str = "http://localhost:5173"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    leaderboard_cache_ttl_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
