from google import (
    genai,
)

from google.genai import (
    types,
)

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

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        api_key: str | None,
        model: str,
        vision_model: str | None = None,
    ):

        if not api_key:

            raise AIConfigurationError(
                "GEMINI_API_KEY is not configured."
            )


        self.model = (
            model
        )


        self.vision_model = (
            vision_model
            or
            model
        )


        self.client = (
            genai.Client(
                api_key=
                    api_key,
            )
        )


    # ========================================================
    # PROVIDER NAME
    # ========================================================

    @property
    def name(
        self,
    ) -> str:

        return "gemini"


    # ========================================================
    # GENERATE SUMMARY FROM TEXT
    #
    # Used by:
    # - Text material
    # - PDF extracted text
    # ========================================================

    def generate_summary(
        self,
        text: str,
    ) -> SummaryContent:

        clean_text = (
            text
            or ""
        ).strip()


        if not clean_text:

            raise AIResponseError(
                "No study content was provided "
                "for summary generation."
            )


        prompt = (
            "You are LearnLoop AI, "
            "an academic study assistant.\n\n"

            "Create a useful revision summary "
            "from the study material below.\n\n"

            "Requirements:\n"
            "- Use only information supported "
            "by the material.\n"
            "- Do not invent facts.\n"
            "- Keep the summary concise but meaningful.\n"
            "- Identify the most important concepts "
            "as key points.\n"
            "- Give short practical study tips.\n\n"

            "STUDY MATERIAL:\n\n"

            f"{clean_text}"
        )


        try:

            interaction = (
                self.client
                .interactions
                .create(
                    model=
                        self.model,

                    input=
                        prompt,

                    response_format={
                        "type":
                            "text",

                        "mime_type":
                            "application/json",

                        "schema":
                            SummaryContent
                            .model_json_schema(),
                    },
                )
            )


            response_text = (
                interaction
                .output_text

                or
                ""
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

            print(
                "[Gemini text summary error]"
            )

            print(
                "Type:",
                type(exc).__name__,
            )

            print(
                "Message:",
                str(exc),
            )

            print(
                "Model:",
                self.model,
            )


            raise AIResponseError(
                "Gemini summary generation failed."
            ) from exc


    # ========================================================
    # NORMALIZE IMAGE MIME
    # ========================================================

    @staticmethod
    def _normalize_image_mime_type(
        mime_type: str | None,
    ) -> str:

        normalized = (
            mime_type
            or ""
        ).strip().lower()


        aliases = {

            "image/jpg":
                "image/jpeg",

            "image/pjpeg":
                "image/jpeg",

            "image/x-png":
                "image/png",
        }


        return (
            aliases.get(
                normalized,
                normalized,
            )
        )


    # ========================================================
    # DETECT IMAGE MIME FROM ACTUAL BYTES
    # ========================================================

    @staticmethod
    def _detect_image_mime_type(
        image_bytes: bytes,
    ) -> str | None:

        # JPEG

        if (
            len(image_bytes) >= 3
            and
            image_bytes.startswith(
                b"\xFF\xD8\xFF"
            )
        ):

            return "image/jpeg"


        # PNG

        if (
            len(image_bytes) >= 8
            and
            image_bytes.startswith(
                b"\x89PNG\r\n\x1a\n"
            )
        ):

            return "image/png"


        # WEBP

        if (
            len(image_bytes) >= 12
            and
            image_bytes[0:4] ==
                b"RIFF"
            and
            image_bytes[8:12] ==
                b"WEBP"
        ):

            return "image/webp"


        return None


    # ========================================================
    # RESOLVE IMAGE MIME
    # ========================================================

    def _resolve_image_mime_type(
        self,
        image_bytes: bytes,
        declared_mime_type: str | None,
    ) -> str:

        detected_mime_type = (
            self._detect_image_mime_type(
                image_bytes
            )
        )


        if detected_mime_type:

            return (
                detected_mime_type
            )


        normalized_mime_type = (
            self._normalize_image_mime_type(
                declared_mime_type
            )
        )


        supported = {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/heic",
            "image/heif",
        }


        if (
            normalized_mime_type
            not in supported
        ):

            raise AIResponseError(
                "Unsupported image MIME type: "
                f"{declared_mime_type or 'unknown'}"
            )


        return (
            normalized_mime_type
        )


    # ========================================================
    # FINISH REASON HELPER
    # ========================================================

    @staticmethod
    def _get_finish_reason(
        response,
    ) -> str:

        candidates = (
            getattr(
                response,
                "candidates",
                None,
            )
            or
            []
        )


        if not candidates:

            return "NO_CANDIDATE"


        finish_reason = getattr(
            candidates[0],
            "finish_reason",
            None,
        )


        if finish_reason is None:

            return "UNKNOWN"


        enum_value = getattr(
            finish_reason,
            "value",
            None,
        )


        if enum_value is not None:

            return str(
                enum_value
            )


        return str(
            finish_reason
        )


    # ========================================================
    # DIRECT IMAGE SUMMARY
    #
    # Used by:
    # - Gallery image
    # - Camera image
    #
    # IMPORTANT:
    # We intentionally DO NOT request verbatim transcription.
    # This avoids the RECITATION failure seen with code/
    # lecture screenshots.
    # ========================================================

    def generate_summary_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> SummaryContent:

        if not image_bytes:

            raise AIResponseError(
                "The image file is empty."
            )


        resolved_mime_type = (
            self._resolve_image_mime_type(
                image_bytes=
                    image_bytes,

                declared_mime_type=
                    mime_type,
            )
        )


        print(
            "[Gemini direct image summary]"
        )

        print(
            "Vision model:",
            self.vision_model,
        )

        print(
            "Declared MIME:",
            mime_type,
        )

        print(
            "Resolved MIME:",
            resolved_mime_type,
        )

        print(
            "Image bytes:",
            len(image_bytes),
        )


        # ====================================================
        # PROMPT
        #
        # Deliberately asks for understanding/paraphrasing,
        # NOT full transcription.
        # ====================================================

        prompt = (
            "You are LearnLoop AI, "
            "an academic study assistant.\n\n"

            "Analyze the attached image as study material "
            "and create revision notes from what is visibly "
            "understandable.\n\n"

            "The image may contain:\n"
            "- a lecture screenshot\n"
            "- source code in an IDE\n"
            "- terminal output\n"
            "- presentation slides\n"
            "- diagrams\n"
            "- printed notes\n"
            "- handwritten notes\n\n"

            "Requirements:\n"

            "- Summarize and explain the educational content "
            "instead of transcribing it verbatim.\n"

            "- Do NOT reproduce large passages of text "
            "or source code word-for-word.\n"

            "- If source code is visible, explain what the "
            "code is doing and identify important programming "
            "concepts, classes, methods, APIs or patterns.\n"

            "- Very short identifiers or code fragments may "
            "be mentioned only when needed for understanding.\n"

            "- If a diagram is visible, explain its main "
            "technical idea or relationship.\n"

            "- Ignore unrelated application chrome, toolbars, "
            "meeting controls and desktop UI.\n"

            "- Do not invent text that cannot be read.\n"

            "- Use only information reasonably supported "
            "by the visible image.\n"

            "- Create a concise but useful summary.\n"

            "- Provide the important key points a student "
            "should remember.\n"

            "- Provide practical study tips based on "
            "the concepts visible in the image.\n"
        )


        try:

            # =================================================
            # IMAGE INPUT
            # =================================================

            image_part = (
                types.Part.from_bytes(
                    data=
                        image_bytes,

                    mime_type=
                        resolved_mime_type,
                )
            )


            # =================================================
            # STRUCTURED MULTIMODAL GENERATION
            # =================================================

            response = (
                self.client
                .models
                .generate_content(
                    model=
                        self.vision_model,

                    contents=[
                        prompt,
                        image_part,
                    ],

                    config=
                        types.GenerateContentConfig(
                            temperature=
                                0.2,

                            media_resolution=
                                types
                                .MediaResolution
                                .MEDIA_RESOLUTION_HIGH,

                            response_mime_type=
                                "application/json",

                            response_schema=
                                SummaryContent,
                        ),
                )
            )


            # =================================================
            # PREFER SDK PARSED RESPONSE
            # =================================================

            parsed = getattr(
                response,
                "parsed",
                None,
            )


            if isinstance(
                parsed,
                SummaryContent,
            ):

                print(
                    "[Gemini direct image summary success]"
                )

                return parsed


            # =================================================
            # FALLBACK TO RAW JSON TEXT
            # =================================================

            response_text = (
                response.text
                or
                ""
            ).strip()


            if not response_text:

                finish_reason = (
                    self._get_finish_reason(
                        response
                    )
                )


                print(
                    "[Gemini image summary empty]"
                )

                print(
                    "Finish reason:",
                    finish_reason,
                )


                raise AIResponseError(
                    "Gemini could not generate "
                    "a summary from this image. "
                    f"Finish reason: {finish_reason}"
                )


            summary = (
                SummaryContent
                .model_validate_json(
                    response_text
                )
            )


            print(
                "[Gemini direct image summary success]"
            )


            return summary


        except AIResponseError:

            raise


        except Exception as exc:

            print(
                "[Gemini direct image summary error]"
            )

            print(
                "Type:",
                type(exc).__name__,
            )

            print(
                "Message:",
                str(exc),
            )

            print(
                "Vision model:",
                self.vision_model,
            )

            print(
                "Resolved MIME:",
                resolved_mime_type,
            )


            raise AIResponseError(
                "Gemini image summary generation failed."
            ) from exc


    # ========================================================
    # IMAGE TEXT EXTRACTION
    #
    # Retained only for future features.
    #
    # Material AI summary DOES NOT use this anymore because
    # verbatim extraction can trigger RECITATION.
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


        resolved_mime_type = (
            self._resolve_image_mime_type(
                image_bytes=
                    image_bytes,

                declared_mime_type=
                    mime_type,
            )
        )


        prompt = (
            "Analyze this study image and produce "
            "brief paraphrased notes about the readable "
            "educational content. "

            "Do not copy large passages or source code "
            "verbatim. "

            "If code is visible, describe the programming "
            "concepts and behavior instead of transcribing "
            "the complete code."
        )


        try:

            image_part = (
                types.Part.from_bytes(
                    data=
                        image_bytes,

                    mime_type=
                        resolved_mime_type,
                )
            )


            response = (
                self.client
                .models
                .generate_content(
                    model=
                        self.vision_model,

                    contents=[
                        prompt,
                        image_part,
                    ],

                    config=
                        types.GenerateContentConfig(
                            temperature=
                                0.2,

                            media_resolution=
                                types
                                .MediaResolution
                                .MEDIA_RESOLUTION_HIGH,
                        ),
                )
            )


            response_text = (
                response.text
                or
                ""
            ).strip()


            if not response_text:

                finish_reason = (
                    self._get_finish_reason(
                        response
                    )
                )


                raise AIResponseError(
                    "Gemini returned no usable "
                    "image notes. "
                    f"Finish reason: {finish_reason}"
                )


            return response_text


        except AIResponseError:

            raise


        except Exception as exc:

            print(
                "[Gemini image analysis error]",
                type(exc).__name__,
                str(exc),
            )


            raise AIResponseError(
                "Gemini image analysis failed."
            ) from exc