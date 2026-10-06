from typing import Literal

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(
    BaseSettings
):

    # ========================================================
    # APPLICATION
    # ========================================================

    app_name: str = (
        "LearnLoop AI Backend"
    )

    app_version: str = (
        "1.0.0"
    )

    environment: str = (
        "development"
    )


    # ========================================================
    # DATABASE
    # ========================================================

    database_url: (
        str
        | None
    ) = None


    # ========================================================
    # AUTHENTICATION
    # ========================================================

    jwt_secret_key: (
        str
        | None
    ) = None

    jwt_algorithm: str = (
        "HS256"
    )

    jwt_access_token_expire_minutes: int = (
        60
    )


    # ========================================================
    # AI PROVIDER
    # ========================================================

    ai_provider: Literal[
        "gemini",
        "openai",
    ] = "gemini"


    # ========================================================
    # GEMINI
    # ========================================================

    gemini_api_key: (
        str
        | None
    ) = None


    # Used for:
    # - text summaries
    # - extracted PDF text
    # - general structured AI tasks

    gemini_model: str = (
        "gemini-3.5-flash-lite"
    )


    # Used for:
    # - screenshots
    # - source-code screenshots
    # - gallery images
    # - camera images
    # - visually dense study content

    gemini_vision_model: str = (
        "gemini-3.5-flash"
    )


    # ========================================================
    # OPENAI
    # ========================================================

    openai_api_key: (
        str
        | None
    ) = None

    openai_model: str = (
        ""
    )


    # ========================================================
    # SETTINGS CONFIG
    # ========================================================

    model_config = (
        SettingsConfigDict(
            env_file=
                ".env",

            env_file_encoding=
                "utf-8",

            case_sensitive=
                False,

            extra=
                "ignore",
        )
    )


settings = Settings()