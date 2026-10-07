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

from app.schemas.quiz import (
    QuizGenerationContent,
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

        image_bytes = (
            self._read_image(
                file_path
            )
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

        image_bytes = (
            self._read_image(
                file_path
            )
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
            card_count < 4
            or
            card_count > 20
        ):

            raise ValueError(
                "Flashcard count must be "
                "between 4 and 20."
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
            card_count < 4
            or
            card_count > 20
        ):

            raise ValueError(
                "Flashcard count must be "
                "between 4 and 20."
            )


        image_bytes = (
            self._read_image(
                file_path
            )
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


    # ========================================================
    # TEXT QUIZ
    #
    # Used by:
    # - Text material
    # - PDF extracted text
    # ========================================================

    def generate_quiz(
        self,
        text: str,
        question_count: int = 10,
    ) -> QuizGenerationContent:

        clean_text = (
            text
            or
            ""
        ).strip()


        if not clean_text:

            raise AIResponseError(
                "No study content was provided "
                "for quiz generation."
            )


        if (
            question_count < 5
            or
            question_count > 20
        ):

            raise ValueError(
                "Quiz question count must be "
                "between 5 and 20."
            )


        result = (
            self.provider
            .generate_quiz(
                text=
                    clean_text,

                question_count=
                    question_count,
            )
        )


        # ====================================================
        # EXACT COUNT CHECK
        # ====================================================

        if (
            len(
                result.questions
            )
            !=
            question_count
        ):

            raise AIResponseError(
                "The AI provider returned "
                f"{len(result.questions)} questions "
                f"instead of {question_count}."
            )


        return result


    # ========================================================
    # IMAGE QUIZ
    #
    # Used by:
    # - Gallery material
    # - Camera material
    # ========================================================

    def generate_quiz_from_image(
        self,
        file_path: Path,
        mime_type: str,
        question_count: int = 10,
    ) -> QuizGenerationContent:

        if (
            question_count < 5
            or
            question_count > 20
        ):

            raise ValueError(
                "Quiz question count must be "
                "between 5 and 20."
            )


        image_bytes = (
            self._read_image(
                file_path
            )
        )


        result = (
            self.provider
            .generate_quiz_from_image(
                image_bytes=
                    image_bytes,

                mime_type=
                    mime_type,

                question_count=
                    question_count,
            )
        )


        if (
            len(
                result.questions
            )
            !=
            question_count
        ):

            raise AIResponseError(
                "The AI provider returned "
                f"{len(result.questions)} questions "
                f"instead of {question_count}."
            )


        return result


    # ========================================================
    # READ IMAGE
    # ========================================================

    def _read_image(
        self,
        file_path: Path,
    ) -> bytes:

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


        return image_bytes