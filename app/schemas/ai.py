from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# EXTRACTION
# ============================================================


class MaterialExtractionResponse(
    BaseModel
):
    material_id: int

    title: str

    source_type: str

    text: str

    character_count: int


# ============================================================
# INTERNAL STRUCTURED AI RESULT
# ============================================================


class SummaryContent(
    BaseModel
):
    summary: str = Field(
        description=(
            "A concise but useful summary "
            "of the study material."
        )
    )

    key_points: list[str] = Field(
        description=(
            "Important facts and concepts "
            "the student should remember."
        )
    )

    study_tips: list[str] = Field(
        description=(
            "Short suggestions for studying "
            "or revising this material."
        )
    )


# ============================================================
# API RESPONSE
# ============================================================


class MaterialSummaryResponse(
    BaseModel
):
    material_id: int

    title: str

    source_type: str

    provider: str

    extracted_character_count: int

    summary: str

    key_points: list[str]

    study_tips: list[str]