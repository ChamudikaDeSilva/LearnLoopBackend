from sqlalchemy.orm import (
    Session,
)

from app.models.material import (
    Material,
)

from app.models.material_summary import (
    MaterialSummary,
)

from app.models.user import (
    User,
)

from app.repositories.material_summary_repository import (
    MaterialSummaryRepository,
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


# ============================================================
# EXCEPTIONS
# ============================================================


class MaterialSummaryNotFoundError(
    Exception
):
    pass


# ============================================================
# MATERIAL AI SERVICE
# ============================================================


class MaterialAIService:

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        material_service:
            MaterialService,
        db:
            Session,
        ai_service:
            AIService | None = None,
    ):

        self.material_service = (
            material_service
        )


        self.extraction_service = (
            ContentExtractionService()
        )


        self.ai_service = (
            ai_service
            or
            AIService()
        )


        self.summary_repository = (
            MaterialSummaryRepository(
                db
            )
        )


    # ========================================================
    # GET TEXT / PDF CONTENT
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
    # MAP STORED RECORD TO API RESPONSE
    # ========================================================

    def _to_response(
        self,
        material: Material,
        stored: MaterialSummary,
    ) -> MaterialSummaryResponse:

        return MaterialSummaryResponse(
            material_id=
                material.id,

            title=
                material.title,

            source_type=
                stored.source_type,

            provider=
                stored.provider,

            extracted_character_count=
                stored
                .extracted_character_count,

            summary=
                stored.summary,

            key_points=
                list(
                    stored.key_points
                    or
                    []
                ),

            study_tips=
                list(
                    stored.study_tips
                    or
                    []
                ),
        )


    # ========================================================
    # SAVE GENERATED SUMMARY
    # ========================================================

    def _save_summary(
        self,
        *,
        material: Material,
        extracted_character_count: int,
        summary_text: str,
        key_points: list[str],
        study_tips: list[str],
    ) -> MaterialSummaryResponse:

        stored = (
            self.summary_repository
            .upsert(
                material_id=
                    material.id,

                provider=
                    self.ai_service
                    .provider_name,

                source_type=
                    material.source_type,

                extracted_character_count=
                    extracted_character_count,

                summary=
                    summary_text,

                key_points=
                    key_points,

                study_tips=
                    study_tips,
            )
        )


        return (
            self._to_response(
                material,
                stored,
            )
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


        generated = (
            self.ai_service
            .generate_summary(
                extracted.text
            )
        )


        return (
            self._save_summary(
                material=
                    material,

                extracted_character_count=
                    extracted
                    .character_count,

                summary_text=
                    generated.summary,

                key_points=
                    generated.key_points,

                study_tips=
                    generated.study_tips,
            )
        )


    # ========================================================
    # GENERATE IMAGE / CAMERA SUMMARY
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


        generated = (
            self.ai_service
            .generate_summary_from_image(
                file_path=
                    file_path,

                mime_type=
                    mime_type,
            )
        )


        return (
            self._save_summary(
                material=
                    material,

                # No intermediate OCR/transcript
                # exists for direct multimodal summary.
                extracted_character_count=
                    0,

                summary_text=
                    generated.summary,

                key_points=
                    generated.key_points,

                study_tips=
                    generated.study_tips,
            )
        )


    # ========================================================
    # GENERATE / REGENERATE SUMMARY
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


        raise UnsupportedContentTypeError(
            "Unsupported material source type: "
            f"{material.source_type}"
        )


    # ========================================================
    # GET SAVED SUMMARY
    # ========================================================

    def get_saved_summary(
        self,
        material_id: int,
        current_user: User,
    ) -> MaterialSummaryResponse:

        # This also verifies ownership.
        material = (
            self.material_service
            .get_material(
                material_id,
                current_user,
            )
        )


        stored = (
            self.summary_repository
            .get_by_material_id(
                material.id
            )
        )


        if stored is None:

            raise (
                MaterialSummaryNotFoundError()
            )


        return (
            self._to_response(
                material,
                stored,
            )
        )