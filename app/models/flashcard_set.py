from datetime import (
    datetime,
)

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import (
    Base,
)


class FlashcardSet(
    Base
):

    __tablename__ = (
        "flashcard_sets"
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
    # One material = one current flashcard set.
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
    # AI PROVIDER
    # ========================================================

    provider: Mapped[str] = (
        mapped_column(
            String(50),
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
            server_default=
                func.now(),
        )
    )


    updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            nullable=False,
            server_default=
                func.now(),
            onupdate=
                func.now(),
        )
    )