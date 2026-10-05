from app.ai.providers.base import (
    AIConfigurationError,
    AIProvider,
)

from app.ai.providers.gemini_provider import (
    GeminiProvider,
)

from app.ai.providers.openai_provider import (
    OpenAIProvider,
)

from app.core.config import (
    settings,
)


def create_ai_provider(
) -> AIProvider:
    provider_name = (
        settings.ai_provider
        .strip()
        .lower()
    )

    if provider_name == "gemini":
        return GeminiProvider(
            api_key=(
                settings.gemini_api_key
            ),
            model=(
                settings.gemini_model
            ),
        )

    if provider_name == "openai":
        return OpenAIProvider(
            api_key=(
                settings.openai_api_key
            ),
            model=(
                settings.openai_model
            ),
        )

    raise AIConfigurationError(
        f"Unsupported AI provider: {provider_name}"
    )
