import base64

from openai import OpenAI

from app.ai.providers.base import (
    AIConfigurationError,
    AIProvider,
    AIResponseError,
)

from app.schemas.ai import (
    SummaryContent,
)


class OpenAIProvider(
    AIProvider
):

    def __init__(
        self,
        api_key: str | None,
        model: str,
    ):
        if not api_key:
            raise AIConfigurationError(
                "OPENAI_API_KEY is not configured."
            )

        self.model = model

        self.client = OpenAI(
            api_key=api_key,
        )

    @property
    def name(
        self,
    ) -> str:
        return "openai"

    # ========================================================
    # SUMMARY
    # ========================================================

    def generate_summary(
        self,
        text: str,
    ) -> SummaryContent:
        try:
            response = (
                self.client
                .responses
                .parse(
                    model=self.model,
                    input=[
                        {
                            "role": "system",
                            "content": (
                                "You are LearnLoop AI, an academic "
                                "study assistant. Use only information "
                                "supported by the supplied study material. "
                                "Do not invent facts."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                "Create a concise but meaningful study "
                                "summary, important key points and short "
                                "practical study tips from the following "
                                "material:\n\n"
                                f"{text}"
                            ),
                        },
                    ],
                    text_format=SummaryContent,
                )
            )

            result = response.output_parsed

            if result is None:
                raise AIResponseError(
                    "OpenAI returned no structured summary."
                )

            return result

        except AIResponseError:
            raise

        except Exception as exc:
            raise AIResponseError(
                "OpenAI summary generation failed."
            ) from exc

    # ========================================================
    # IMAGE / CAMERA TEXT EXTRACTION
    # ========================================================

    def extract_text_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        if not image_bytes:
            raise AIResponseError(
                "The image file is empty."
            )

        encoded_image = (
            base64.b64encode(
                image_bytes
            )
            .decode("utf-8")
        )

        data_url = (
            f"data:{mime_type};"
            f"base64,{encoded_image}"
        )

        try:
            response = (
                self.client
                .responses
                .create(
                    model=self.model,
                    input=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "input_text",
                                    "text": (
                                        "Extract useful study text from "
                                        "this image. Preserve readable "
                                        "headings, labels, definitions, "
                                        "formulas and lists. Do not describe "
                                        "the visual appearance and do not "
                                        "invent missing text. Return only "
                                        "the extracted study content."
                                    ),
                                },
                                {
                                    "type": "input_image",
                                    "image_url": data_url,
                                    "detail": "auto",
                                },
                            ],
                        }
                    ],
                )
            )

            return (
                response.output_text
                or ""
            ).strip()

        except Exception as exc:
            raise AIResponseError(
                "OpenAI image text extraction failed."
            ) from exc
