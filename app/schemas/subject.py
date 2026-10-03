from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class SubjectCreateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class SubjectUpdateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class SubjectResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )