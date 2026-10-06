from pathlib import (
    Path,
)

from app.ai.provider_factory import (
    create_ai_provider,
)

from app.ai.providers.base import (
    AIProvider,
    AIResponseError,
)

from app.schemas.ai import (
    SummaryContent,
)

from app.schemas.flashcard import (
    FlashcardGenerationContent,
)


class AIService:

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        provider:
            AIProvider | None = None,
    ):

        self.provider = (
            provider
            or
            create_ai_provider()
        )


    # ========================================================
    # PROVIDER NAME
    # ========================================================

    @property
    def provider_name(
        self,
    ) -> str:

        return (
            self.provider.name
        )


    # ========================================================
    # TEXT SUMMARY
    # ========================================================

    def generate_summary(
        self,
        text: str,
    ) -> SummaryContent:

        clean_text = (
            text
            or
            ""
        ).strip()


        if not clean_text:

            raise AIResponseError(
                "No study content was provided "
                "for summary generation."
            )


        return (
            self.provider
            .generate_summary(
                clean_text
            )
        )


    # ========================================================
    # IMAGE TEXT EXTRACTION
    # ========================================================

    def extract_text_from_image(
        self,
        file_path: Path,
        mime_type: str,
    ) -> str:

        try:

            image_bytes = (
                file_path.read_bytes()
            )

        except OSError as exc:

            raise AIResponseError(
                "Unable to read the stored image."
            ) from exc


        if not image_bytes:

            raise AIResponseError(
                "The stored image is empty."
            )


        return (
            self.provider
            .extract_text_from_image(
                image_bytes=
                    image_bytes,

                mime_type=
                    mime_type,
            )
        )


    # ========================================================
    # DIRECT IMAGE SUMMARY
    # ========================================================

    def generate_summary_from_image(
        self,
        file_path: Path,
        mime_type: str,
    ) -> SummaryContent:

        try:

            image_bytes = (
                file_path.read_bytes()
            )

        except OSError as exc:

            raise AIResponseError(
                "Unable to read the stored image."
            ) from exc


        if not image_bytes:

            raise AIResponseError(
                "The stored image is empty."
            )


        return (
            self.provider
            .generate_summary_from_image(
                image_bytes=
                    image_bytes,

                mime_type=
                    mime_type,
            )
        )


    # ========================================================
    # TEXT FLASHCARDS
    # ========================================================

    def generate_flashcards(
        self,
        text: str,
        card_count: int = 8,
    ) -> FlashcardGenerationContent:

        clean_text = (
            text
            or
            ""
        ).strip()


        if not clean_text:

            raise AIResponseError(
                "No study content was provided "
                "for flashcard generation."
            )


        if (
            card_count < 1
            or
            card_count > 20
        ):

            raise ValueError(
                "Flashcard count must be "
                "between 1 and 20."
            )


        return (
            self.provider
            .generate_flashcards(
                text=
                    clean_text,

                card_count=
                    card_count,
            )
        )


    # ========================================================
    # IMAGE FLASHCARDS
    # ========================================================

    def generate_flashcards_from_image(
        self,
        file_path: Path,
        mime_type: str,
        card_count: int = 8,
    ) -> FlashcardGenerationContent:

        if (
            card_count < 1
            or
            card_count > 20
        ):

            raise ValueError(
                "Flashcard count must be "
                "between 1 and 20."
            )


        try:

            image_bytes = (
                file_path.read_bytes()
            )

        except OSError as exc:

            raise AIResponseError(
                "Unable to read the stored image."
            ) from exc


        if not image_bytes:

            raise AIResponseError(
                "The stored image is empty."
            )


        return (
            self.provider
            .generate_flashcards_from_image(
                image_bytes=
                    image_bytes,

                mime_type=
                    mime_type,

                card_count=
                    card_count,
            )
        )