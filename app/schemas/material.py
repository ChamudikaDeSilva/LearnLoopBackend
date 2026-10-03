from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


MaterialSourceType = Literal[
    "text",
    "pdf",
    "image",
    "camera",
]


# =========================================================
# CREATE TEXT MATERIAL
# =========================================================

class TextMaterialCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    content: str = Field(
        min_length=1,
        max_length=200000,
    )


# =========================================================
# UPDATE TEXT MATERIAL
# =========================================================

class TextMaterialUpdateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    content: str = Field(
        min_length=1,
        max_length=200000,
    )


# =========================================================
# UPDATE IMAGE TITLE
# =========================================================

class ImageMaterialTitleUpdateRequest(
    BaseModel
):
    title: str = Field(
        min_length=1,
        max_length=200,
    )


# =========================================================
# MATERIAL RESPONSE
# =========================================================

class MaterialResponse(BaseModel):
    id: int

    subject_id: int

    title: str

    source_type: MaterialSourceType

    content: str | None

    file_name: str | None

    file_path: str | None

    mime_type: str | None

    file_size: int | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )