from sqlalchemy import (
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import (
    Base,
)


class Flashcard(
    Base
):

    __tablename__ = (
        "flashcards"
    )


    # ========================================================
    # CONSTRAINTS
    #
    # Prevent two cards in the same set from having the
    # same display position.
    # ========================================================

    __table_args__ = (
        UniqueConstraint(
            "flashcard_set_id",
            "position",
            name=
                "uq_flashcards_set_position",
        ),
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
    # FLASHCARD SET
    # ========================================================

    flashcard_set_id: Mapped[int] = (
        mapped_column(
            Integer,
            ForeignKey(
                "flashcard_sets.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )


    # ========================================================
    # ORDER
    # ========================================================

    position: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )


    # ========================================================
    # CARD CONTENT
    # ========================================================

    front: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )


    back: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )