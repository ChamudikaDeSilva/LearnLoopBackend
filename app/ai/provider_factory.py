from app.ai.providers.base import (
    AIConfigurationError,
    AIProvider,
)

from app.ai.providers.gemini_provider import (
    GeminiProvider,
)

from app.core.config import (
    settings,
)


def create_ai_provider(
) -> AIProvider:

    provider_name = (
        settings
        .ai_provider
        .strip()
        .lower()
    )


    if (
        provider_name
        ==
        "gemini"
    ):

        return GeminiProvider(
            api_key=
                settings
                .gemini_api_key,

            model=
                settings
                .gemini_model,

            vision_model=
                settings
                .gemini_vision_model,
        )


    raise AIConfigurationError(
        "Unsupported AI provider: "
        f"{settings.ai_provider}"
    )