from abc import (
    ABC,
    abstractmethod,
)

from app.schemas.ai import (
    SummaryContent,
)


# ============================================================
# AI EXCEPTIONS
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
# AI PROVIDER CONTRACT
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
    # TEXT SUMMARY
    # ========================================================

    @abstractmethod
    def generate_summary(
        self,
        text: str,
    ) -> SummaryContent:
        pass


    # ========================================================
    # IMAGE TEXT EXTRACTION
    #
    # Kept for future use.
    # Material summary no longer depends on this method.
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
    #
    # Not abstract so other providers do not immediately break.
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