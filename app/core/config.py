from typing import Literal

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    # =========================================================
    # APPLICATION
    # =========================================================

    app_name: str = "LearnLoop AI Backend"
    app_version: str = "1.0.0"
    environment: str = "development"

    # =========================================================
    # DATABASE
    # =========================================================

    database_url: str | None = None

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    jwt_secret_key: str | None = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # =========================================================
    # AI
    # =========================================================

    ai_provider: Literal[
        "gemini",
        "openai",
    ] = "gemini"

    # Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str = "gpt-6-luna"

    # =========================================================
    # PYDANTIC SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
