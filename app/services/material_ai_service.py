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
    EmptyMaterialContentError,
    ExtractedContent,
    UnsupportedContentTypeError,
)

from app.services.material_service import (
    MaterialService,
)


class MaterialAIService:

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
    # GET USABLE MATERIAL TEXT
    # ========================================================

    def get_material_text(
        self,
        material: Material,
        current_user: User,
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

        if (
            material.source_type
            in (
                "image",
                "camera",
            )
        ):
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
                or "image/jpeg"
            )

            extracted_text = (
                self.ai_service
                .extract_text_from_image(
                    file_path=file_path,
                    mime_type=mime_type,
                )
                .strip()
            )

            if not extracted_text:
                raise EmptyMaterialContentError(
                    "No readable study text was "
                    "found in this image."
                )

            return ExtractedContent(
                extracted_text
            )

        raise UnsupportedContentTypeError(
            "Unsupported material source type."
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

        extracted = (
            self.get_material_text(
                material,
                current_user,
            )
        )

        summary = (
            self.ai_service
            .generate_summary(
                extracted.text
            )
        )

        return MaterialSummaryResponse(
            material_id=material.id,
            title=material.title,
            source_type=material.source_type,
            provider=(
                self.ai_service
                .provider_name
            ),
            extracted_character_count=(
                extracted.character_count
            ),
            summary=summary.summary,
            key_points=summary.key_points,
            study_tips=summary.study_tips,
        )
