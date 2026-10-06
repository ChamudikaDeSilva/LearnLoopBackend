from app.models.material import (
    Material,
)

from app.models.user import (
    User,
)

from app.schemas.ai import (
    MaterialSummaryResponse,
)

from app.services.ai_service import (
    AIService,
)

from app.services.content_extraction_service import (
    ContentExtractionService,
    ExtractedContent,
    UnsupportedContentTypeError,
)

from app.services.material_service import (
    MaterialService,
)


class MaterialAIService:

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        material_service: MaterialService,
        ai_service: AIService | None = None,
    ):

        self.material_service = (
            material_service
        )


        self.extraction_service = (
            ContentExtractionService()
        )


        self.ai_service = (
            ai_service
            or AIService()
        )


    # ========================================================
    # GET USABLE TEXT
    #
    # Only Text and PDF use this path now.
    #
    # Image and Camera are summarized directly from the
    # original image through Gemini multimodal analysis.
    # ========================================================

    def get_material_text(
        self,
        material: Material,
    ) -> ExtractedContent:

        if (
            material.source_type
            in (
                "text",
                "pdf",
            )
        ):

            return (
                self.extraction_service
                .extract(
                    material
                )
            )


        raise UnsupportedContentTypeError(
            "Text extraction is only supported "
            "for text and PDF materials."
        )


    # ========================================================
    # GENERATE TEXT / PDF SUMMARY
    # ========================================================

    def _generate_text_summary(
        self,
        material: Material,
    ) -> MaterialSummaryResponse:

        extracted = (
            self.get_material_text(
                material
            )
        )


        summary = (
            self.ai_service
            .generate_summary(
                extracted.text
            )
        )


        return MaterialSummaryResponse(
            material_id=
                material.id,

            title=
                material.title,

            source_type=
                material.source_type,

            provider=
                self.ai_service
                .provider_name,

            extracted_character_count=
                extracted
                .character_count,

            summary=
                summary.summary,

            key_points=
                summary.key_points,

            study_tips=
                summary.study_tips,
        )


    # ========================================================
    # GENERATE IMAGE / CAMERA SUMMARY
    #
    # IMPORTANT:
    # No verbatim OCR step occurs here.
    #
    # Image
    #   ↓
    # Gemini multimodal understanding
    #   ↓
    # SummaryContent
    # ========================================================

    def _generate_image_summary(
        self,
        material: Material,
        current_user: User,
    ) -> MaterialSummaryResponse:

        (
            _,
            file_path,
        ) = (
            self.material_service
            .get_material_file(
                material.id,
                current_user,
            )
        )


        mime_type = (
            material.mime_type
            or
            "image/jpeg"
        )


        summary = (
            self.ai_service
            .generate_summary_from_image(
                file_path=
                    file_path,

                mime_type=
                    mime_type,
            )
        )


        return MaterialSummaryResponse(
            material_id=
                material.id,

            title=
                material.title,

            source_type=
                material.source_type,

            provider=
                self.ai_service
                .provider_name,

            # No intermediate text extraction
            # occurs for image/camera summary.
            extracted_character_count=
                0,

            summary=
                summary.summary,

            key_points=
                summary.key_points,

            study_tips=
                summary.study_tips,
        )


    # ========================================================
    # GENERATE SUMMARY
    # ========================================================

    def generate_summary(
        self,
        material_id: int,
        current_user: User,
    ) -> MaterialSummaryResponse:

        material = (
            self.material_service
            .get_material(
                material_id,
                current_user,
            )
        )


        # ====================================================
        # TEXT / PDF
        # ====================================================

        if (
            material.source_type
            in (
                "text",
                "pdf",
            )
        ):

            return (
                self._generate_text_summary(
                    material
                )
            )


        # ====================================================
        # IMAGE / CAMERA
        # ====================================================

        if (
            material.source_type
            in (
                "image",
                "camera",
            )
        ):

            return (
                self._generate_image_summary(
                    material=
                        material,

                    current_user=
                        current_user,
                )
            )


        # ====================================================
        # UNSUPPORTED
        # ====================================================

        raise UnsupportedContentTypeError(
            "Unsupported material source type: "
            f"{material.source_type}"
        )