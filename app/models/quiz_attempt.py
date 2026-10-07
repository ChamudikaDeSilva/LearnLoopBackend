from datetime import (
    datetime,
)

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import (
    Base,
)


class QuizAttempt(
    Base
):

    __tablename__ = (
        "quiz_attempts"
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
    # QUIZ
    # ========================================================

    quiz_id: Mapped[int] = (
        mapped_column(
            Integer,
            ForeignKey(
                "material_quizzes.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )


    # ========================================================
    # USER
    # ========================================================

    user_id: Mapped[int] = (
        mapped_column(
            Integer,
            ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )


    # ========================================================
    # RESULT
    # ========================================================

    score: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )


    total_questions: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )


    # ========================================================
    # SUBMITTED
    # ========================================================

    submitted_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            nullable=False,
            server_default=
                func.now(),
        )
    )