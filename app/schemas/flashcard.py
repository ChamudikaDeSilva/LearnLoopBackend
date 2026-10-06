from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# ONE GENERATED FLASHCARD
# ============================================================


class FlashcardContent(
    BaseModel
):

    front: str = Field(
        min_length=1,
        description=(
            "A concise study question, "
            "term, or recall prompt."
        ),
    )

    back: str = Field(
        min_length=1,
        description=(
            "A concise and accurate answer "
            "to the flashcard prompt."
        ),
    )


# ============================================================
# GEMINI STRUCTURED OUTPUT
# ============================================================


class FlashcardGenerationContent(
    BaseModel
):

    cards: list[
        FlashcardContent
    ] = Field(
        min_length=1,
        description=(
            "The generated study flashcards."
        ),
    )


# ============================================================
# SAVED CARD RESPONSE
# ============================================================


class FlashcardItemResponse(
    BaseModel
):

    id: int

    position: int

    front: str

    back: str


# ============================================================
# MATERIAL FLASHCARD SET RESPONSE
# ============================================================


class MaterialFlashcardsResponse(
    BaseModel
):

    flashcard_set_id: int

    material_id: int

    title: str

    source_type: str

    provider: str

    card_count: int

    cards: list[
        FlashcardItemResponse
    ]