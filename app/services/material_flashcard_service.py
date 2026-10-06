from sqlalchemy.orm import (
    Session,
)

from app.models.flashcard import (
    Flashcard,
)

from app.models.flashcard_set import (
    FlashcardSet,
)

from app.models.material import (
    Material,
)

from app.models.user import (
    User,
)

from app.repositories.flashcard_repository import (
    FlashcardRepository,
)

from app.schemas.flashcard import (
    FlashcardGenerationContent,
    FlashcardItemResponse,
    MaterialFlashcardsResponse,
)

from app.services.ai_service import (
    AIService,
)

from app.services.content_extraction_service import (
    ContentExtractionService,
    UnsupportedContentTypeError,
)

from app.services.material_service import (
    MaterialService,
)


# ============================================================
# CONSTANTS
# ============================================================


DEFAULT_FLASHCARD_COUNT = 8


# ============================================================
# EXCEPTIONS
# ============================================================


class FlashcardSetNotFoundError(
    Exception
):
    pass


# ============================================================
# MATERIAL FLASHCARD SERVICE
# ============================================================


class MaterialFlashcardService:

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


        self.flashcard_repository = (
            FlashcardRepository(
                db
            )
        )


    # ========================================================
    # MAP RESPONSE
    # ========================================================

    def _to_response(
        self,
        material: Material,
        flashcard_set: FlashcardSet,
        cards: list[Flashcard],
    ) -> MaterialFlashcardsResponse:

        return (
            MaterialFlashcardsResponse(
                flashcard_set_id=
                    flashcard_set.id,

                material_id=
                    material.id,

                title=
                    material.title,

                source_type=
                    material.source_type,

                provider=
                    flashcard_set.provider,

                card_count=
                    len(
                        cards
                    ),

                cards=[
                    FlashcardItemResponse(
                        id=
                            card.id,

                        position=
                            card.position,

                        front=
                            card.front,

                        back=
                            card.back,
                    )
                    for card
                    in cards
                ],
            )
        )


    # ========================================================
    # SAVE GENERATED DECK
    # ========================================================

    def _save(
        self,
        material: Material,
        generated:
            FlashcardGenerationContent,
    ) -> MaterialFlashcardsResponse:

        if not generated.cards:

            raise ValueError(
                "No flashcards were generated."
            )


        (
            flashcard_set,
            cards,
        ) = (
            self.flashcard_repository
            .replace(
                material_id=
                    material.id,

                provider=
                    self.ai_service
                    .provider_name,

                cards=
                    generated.cards,
            )
        )


        return (
            self._to_response(
                material=
                    material,

                flashcard_set=
                    flashcard_set,

                cards=
                    cards,
            )
        )


    # ========================================================
    # GENERATE TEXT / PDF
    # ========================================================

    def _generate_from_text(
        self,
        material: Material,
        card_count: int,
    ) -> MaterialFlashcardsResponse:

        extracted = (
            self.extraction_service
            .extract(
                material
            )
        )


        generated = (
            self.ai_service
            .generate_flashcards(
                text=
                    extracted.text,

                card_count=
                    card_count,
            )
        )


        return (
            self._save(
                material=
                    material,

                generated=
                    generated,
            )
        )


    # ========================================================
    # GENERATE IMAGE / CAMERA
    # ========================================================

    def _generate_from_image(
        self,
        material: Material,
        current_user: User,
        card_count: int,
    ) -> MaterialFlashcardsResponse:

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
            .generate_flashcards_from_image(
                file_path=
                    file_path,

                mime_type=
                    mime_type,

                card_count=
                    card_count,
            )
        )


        return (
            self._save(
                material=
                    material,

                generated=
                    generated,
            )
        )


    # ========================================================
    # GENERATE / REGENERATE
    # ========================================================

    def generate(
        self,
        material_id: int,
        current_user: User,
        card_count: int =
            DEFAULT_FLASHCARD_COUNT,
    ) -> MaterialFlashcardsResponse:

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
                self._generate_from_text(
                    material=
                        material,

                    card_count=
                        card_count,
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
                self._generate_from_image(
                    material=
                        material,

                    current_user=
                        current_user,

                    card_count=
                        card_count,
                )
            )


        raise UnsupportedContentTypeError(
            "Unsupported material source type: "
            f"{material.source_type}"
        )


    # ========================================================
    # GET SAVED FLASHCARDS
    # ========================================================

    def get_saved(
        self,
        material_id: int,
        current_user: User,
    ) -> MaterialFlashcardsResponse:

        # Ownership validation
        material = (
            self.material_service
            .get_material(
                material_id,
                current_user,
            )
        )


        result = (
            self.flashcard_repository
            .get_by_material_id(
                material.id
            )
        )


        if result is None:

            raise (
                FlashcardSetNotFoundError()
            )


        (
            flashcard_set,
            cards,
        ) = result


        return (
            self._to_response(
                material=
                    material,

                flashcard_set=
                    flashcard_set,

                cards=
                    cards,
            )
        )