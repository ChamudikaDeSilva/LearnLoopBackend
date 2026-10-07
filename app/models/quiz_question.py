from sqlalchemy import (
    ForeignKey,
    Integer,
    JSON,
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


class QuizQuestion(
    Base
):

    __tablename__ = (
        "quiz_questions"
    )


    # ========================================================
    # CONSTRAINTS
    # ========================================================

    __table_args__ = (

        UniqueConstraint(
            "quiz_id",
            "position",
            name=
                "uq_quiz_questions_quiz_position",
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
    # DISPLAY ORDER
    # ========================================================

    position: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )


    # ========================================================
    # QUESTION
    # ========================================================

    question: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )


    # ========================================================
    # OPTIONS
    #
    # Example:
    #
    # [
    #   "Docker Engine",
    #   "Docker Hub",
    #   "Docker Compose",
    #   "Docker Desktop"
    # ]
    # ========================================================

    options: Mapped[list] = (
        mapped_column(
            JSON,
            nullable=False,
        )
    )


    # ========================================================
    # CORRECT OPTION
    #
    # 0 = first option
    # 1 = second option
    # 2 = third option
    # 3 = fourth option
    #
    # IMPORTANT:
    # Do NOT expose this in the normal quiz API response.
    # ========================================================

    correct_index: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )


    # ========================================================
    # EXPLANATION
    #
    # Returned after submission.
    # ========================================================

    explanation: Mapped[str] = (
        mapped_column(
            Text,
            nullable=False,
        )
    )