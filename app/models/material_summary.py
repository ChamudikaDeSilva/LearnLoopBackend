from datetime import (
    datetime,
)

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import (
    Base,
)


class MaterialSummary(
    Base
):

    __tablename__ = (
        "material_summaries"
    )


    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[int] = (
        mapped_column(
            Integer,
            primary_key=True,
            index=True,
        )
    )


    # ========================================================
    # MATERIAL
    #
    # One material = one current summary.
    # ========================================================

    material_id: Mapped[int] = (
        mapped_column(
            Integer,
            ForeignKey(
                "materials.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            unique=True,
            index=True,
        )
    )


    # ========================================================
    # AI METADATA
    # ========================================================

    provider: Mapped[str] = (
        mapped_column(
            String(50),
            nullable=False,
        )
    )


    source_type: Mapped[str] = (
        mapped_column(
            String(20),
            nullable=False,
        )
    )


    extracted_character_count: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
            default=0,
        )
    )


    # ========================================================
    # GENERATED CONTENT
    # ========================================================

    summary: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )


    key_points: Mapped[list] = (
        mapped_column(
            JSON,
            nullable=False,
        )
    )


    study_tips: Mapped[list] = (
        mapped_column(
            JSON,
            nullable=False,
        )
    )


    # ========================================================
    # TIMESTAMPS
    # ========================================================

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            nullable=False,
            server_default=func.now(),
        )
    )


    updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )