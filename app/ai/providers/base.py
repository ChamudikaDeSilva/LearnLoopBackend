from abc import (
    ABC,
    abstractmethod,
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


# ============================================================
# EXCEPTIONS
# ============================================================


class AIProviderError(
    Exception
):
    pass


class AIConfigurationError(
    AIProviderError
):
    pass


class AIResponseError(
    AIProviderError
):
    pass


# ============================================================
# AI PROVIDER
# ============================================================


class AIProvider(
    ABC
):

    # ========================================================
    # PROVIDER NAME
    # ========================================================

    @property
    @abstractmethod
    def name(
        self,
    ) -> str:
        pass


    # ========================================================
    # SUMMARY
    # ========================================================

    @abstractmethod
    def generate_summary(
        self,
        text: str,
    ) -> SummaryContent:
        pass


    # ========================================================
    # IMAGE EXTRACTION
    # ========================================================

    @abstractmethod
    def extract_text_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        pass


    # ========================================================
    # DIRECT IMAGE SUMMARY
    # ========================================================

    def generate_summary_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> SummaryContent:

        raise AIResponseError(
            "This AI provider does not support "
            "direct image summary generation."
        )


    # ========================================================
    # TEXT FLASHCARDS
    # ========================================================

    def generate_flashcards(
        self,
        text: str,
        card_count: int,
    ) -> FlashcardGenerationContent:

        raise AIResponseError(
            "This AI provider does not support "
            "flashcard generation."
        )


    # ========================================================
    # IMAGE FLASHCARDS
    # ========================================================

    def generate_flashcards_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        card_count: int,
    ) -> FlashcardGenerationContent:

        raise AIResponseError(
            "This AI provider does not support "
            "direct image flashcard generation."
        )


    # ========================================================
    # TEXT QUIZ
    # ========================================================

    def generate_quiz(
        self,
        text: str,
        question_count: int,
    ) -> QuizGenerationContent:

        raise AIResponseError(
            "This AI provider does not support "
            "quiz generation."
        )


    # ========================================================
    # IMAGE QUIZ
    # ========================================================

    def generate_quiz_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
        question_count: int,
    ) -> QuizGenerationContent:

        raise AIResponseError(
            "This AI provider does not support "
            "direct image quiz generation."
        )