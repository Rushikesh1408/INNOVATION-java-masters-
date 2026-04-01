from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings helper for reusable config access."""

    database_url: str
    app_name: str = "Secure Online Examination System"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)
