from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# EXTRACTION RESPONSE
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
# STRUCTURED SUMMARY CONTENT
# ============================================================


class SummaryContent(
    BaseModel
):
    summary: str = Field(
        min_length=1,
        description=(
            "A concise but useful summary "
            "of the supplied study material."
        ),
    )

    key_points: list[str] = Field(
        default_factory=list,
        description=(
            "Important facts and concepts "
            "the student should remember."
        ),
    )

    study_tips: list[str] = Field(
        default_factory=list,
        description=(
            "Short, practical suggestions "
            "for revising this material."
        ),
    )


# ============================================================
# MATERIAL SUMMARY RESPONSE
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
