from abc import (
    ABC,
    abstractmethod,
)

from app.schemas.ai import (
    SummaryContent,
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
# PROVIDER CONTRACT
# ============================================================


class AIProvider(
    ABC
):

    @property
    @abstractmethod
    def name(
        self,
    ) -> str:
        pass

    @abstractmethod
    def generate_summary(
        self,
        text: str,
    ) -> SummaryContent:
        pass

    @abstractmethod
    def extract_text_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        pass
