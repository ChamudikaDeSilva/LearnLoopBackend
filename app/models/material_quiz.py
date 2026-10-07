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


class MaterialQuiz(
    Base
):

    __tablename__ = (
        "material_quizzes"
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
    # Unlike summaries / flashcards,
    # this is NOT unique.
    #
    # One material can have multiple generated quiz versions.
    # ========================================================

    material_id: Mapped[int] = (
        mapped_column(
            Integer,
            ForeignKey(
                "materials.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )


    # ========================================================
    # PROVIDER
    # ========================================================

    provider: Mapped[str] = (
        mapped_column(
            String(50),
            nullable=False,
        )
    )


    # ========================================================
    # QUESTION COUNT
    # ========================================================

    question_count: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )


    # ========================================================
    # CREATED
    # ========================================================

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            nullable=False,
            server_default=
                func.now(),
        )
    )