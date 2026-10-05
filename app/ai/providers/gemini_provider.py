import base64

from google import genai

from app.ai.providers.base import (
    AIConfigurationError,
    AIProvider,
    AIResponseError,
)

from app.schemas.ai import (
    SummaryContent,
)


class GeminiProvider(
    AIProvider
):

    def __init__(
        self,
        api_key: str | None,
        model: str,
    ):
        if not api_key:
            raise AIConfigurationError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = model

        self.client = genai.Client(
            api_key=api_key,
        )

    @property
    def name(
        self,
    ) -> str:
        return "gemini"

    # ========================================================
    # SUMMARY
    # ========================================================

    def generate_summary(
        self,
        text: str,
    ) -> SummaryContent:
        prompt = (
            "You are LearnLoop AI, an academic study assistant.\n\n"
            "Create a useful revision summary from the study "
            "material below.\n\n"
            "Requirements:\n"
            "- Use only information supported by the material.\n"
            "- Do not invent facts.\n"
            "- Keep the summary concise but meaningful.\n"
            "- Identify the most important concepts as key points.\n"
            "- Give short practical study tips.\n\n"
            "STUDY MATERIAL:\n\n"
            f"{text}"
        )

        try:
            interaction = (
                self.client
                .interactions
                .create(
                    model=self.model,
                    input=prompt,
                    response_format={
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": (
                            SummaryContent
                            .model_json_schema()
                        ),
                    },
                )
            )

            response_text = (
                interaction.output_text
                or ""
            ).strip()

            if not response_text:
                raise AIResponseError(
                    "Gemini returned an empty summary."
                )

            return (
                SummaryContent
                .model_validate_json(
                    response_text
                )
            )

        except AIResponseError:
            raise

        except Exception as exc:
            raise AIResponseError(
                "Gemini summary generation failed."
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

        prompt = (
            "Extract the useful study text from this image. "
            "Preserve headings, labels, definitions, formulas "
            "and lists when they are readable. "
            "Do not describe the visual appearance. "
            "Do not invent missing text. "
            "Return only the extracted study content."
        )

        try:
            interaction = (
                self.client
                .interactions
                .create(
                    model=self.model,
                    input=[
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image",
                            "data": encoded_image,
                            "mime_type": mime_type,
                        },
                    ],
                )
            )

            return (
                interaction.output_text
                or ""
            ).strip()

        except Exception as exc:
            raise AIResponseError(
                "Gemini image text extraction failed."
            ) from exc
