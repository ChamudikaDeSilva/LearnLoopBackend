from pathlib import Path

from app.ai.provider_factory import (
    create_ai_provider,
)

from app.ai.providers.base import (
    AIProvider,
)

from app.schemas.ai import (
    SummaryContent,
)


class AIService:

    def __init__(
        self,
        provider: AIProvider | None = None,
    ):
        self.provider = (
            provider
            or create_ai_provider()
        )

    @property
    def provider_name(
        self,
    ) -> str:
        return self.provider.name

    # ========================================================
    # SUMMARY
    # ========================================================

    def generate_summary(
        self,
        text: str,
    ) -> SummaryContent:
        clean_text = text.strip()

        if not clean_text:
            raise ValueError(
                "AI input text is empty."
            )

        return (
            self.provider
            .generate_summary(
                clean_text
            )
        )

    # ========================================================
    # IMAGE / CAMERA EXTRACTION
    # ========================================================

    def extract_text_from_image(
        self,
        file_path: Path,
        mime_type: str,
    ) -> str:
        image_bytes = (
            file_path.read_bytes()
        )

        return (
            self.provider
            .extract_text_from_image(
                image_bytes=image_bytes,
                mime_type=mime_type,
            )
        )
