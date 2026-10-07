from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.database import (
    Base,
)


class QuizAttemptAnswer(
    Base
):

    __tablename__ = (
        "quiz_attempt_answers"
    )


    # ========================================================
    # CONSTRAINT
    #
    # One answer per question for one attempt.
    # ========================================================

    __table_args__ = (

        UniqueConstraint(
            "attempt_id",
            "question_id",
            name=
                "uq_quiz_attempt_answer_question",
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
    # ATTEMPT
    # ========================================================

    attempt_id: Mapped[int] = (
        mapped_column(
            Integer,
            ForeignKey(
                "quiz_attempts.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )


    # ========================================================
    # QUESTION
    # ========================================================

    question_id: Mapped[int] = (
        mapped_column(
            Integer,
            ForeignKey(
                "quiz_questions.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )


    # ========================================================
    # SELECTED OPTION
    #
    # Nullable means the user left it unanswered.
    # ========================================================

    selected_index: Mapped[
        int | None
    ] = (
        mapped_column(
            Integer,
            nullable=True,
        )
    )


    # ========================================================
    # RESULT
    # ========================================================

    is_correct: Mapped[bool] = (
        mapped_column(
            Boolean,
            nullable=False,
        )
    )