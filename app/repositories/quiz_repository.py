from sqlalchemy.orm import (
    Session,
)

from app.models.material_quiz import (
    MaterialQuiz,
)

from app.models.quiz_attempt import (
    QuizAttempt,
)

from app.models.quiz_attempt_answer import (
    QuizAttemptAnswer,
)

from app.models.quiz_question import (
    QuizQuestion,
)

from app.schemas.quiz import (
    QuizGenerationContent,
)


class QuizRepository:

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        db: Session,
    ):

        self.db = db


    # ========================================================
    # GET QUIZ
    # ========================================================

    def get_by_id(
        self,
        quiz_id: int,
    ) -> MaterialQuiz | None:

        return (
            self.db
            .query(
                MaterialQuiz
            )
            .filter(
                MaterialQuiz.id
                ==
                quiz_id
            )
            .first()
        )


    # ========================================================
    # GET LATEST QUIZ FOR MATERIAL
    # ========================================================

    def get_latest_by_material_id(
        self,
        material_id: int,
    ) -> MaterialQuiz | None:

        return (
            self.db
            .query(
                MaterialQuiz
            )
            .filter(
                MaterialQuiz.material_id
                ==
                material_id
            )
            .order_by(
                MaterialQuiz.id.desc()
            )
            .first()
        )


    # ========================================================
    # GET QUESTIONS
    # ========================================================

    def get_questions(
        self,
        quiz_id: int,
    ) -> list[QuizQuestion]:

        return (
            self.db
            .query(
                QuizQuestion
            )
            .filter(
                QuizQuestion.quiz_id
                ==
                quiz_id
            )
            .order_by(
                QuizQuestion.position.asc()
            )
            .all()
        )


    # ========================================================
    # CREATE NEW QUIZ VERSION
    #
    # IMPORTANT:
    #
    # Unlike flashcards, we do not overwrite the previous
    # quiz. Every regeneration creates a new quiz version.
    # ========================================================

    def create_quiz(
        self,
        *,
        material_id: int,
        provider: str,
        generated:
            QuizGenerationContent,
    ) -> tuple[
        MaterialQuiz,
        list[QuizQuestion],
    ]:

        try:

            quiz = (
                MaterialQuiz(
                    material_id=
                        material_id,

                    provider=
                        provider,

                    question_count=
                        len(
                            generated.questions
                        ),
                )
            )


            self.db.add(
                quiz
            )


            # Obtain generated quiz ID.
            self.db.flush()


            for (
                index,
                item,
            ) in enumerate(
                generated.questions,
                start=1,
            ):

                question = (
                    QuizQuestion(
                        quiz_id=
                            quiz.id,

                        position=
                            index,

                        question=
                            item.question.strip(),

                        options=[
                            option.strip()
                            for option
                            in item.options
                        ],

                        correct_index=
                            item.correct_index,

                        explanation=
                            item.explanation.strip(),
                    )
                )


                self.db.add(
                    question
                )


            self.db.commit()


            self.db.refresh(
                quiz
            )


            questions = (
                self.get_questions(
                    quiz.id
                )
            )


            return (
                quiz,
                questions,
            )


        except Exception:

            self.db.rollback()

            raise


    # ========================================================
    # CREATE QUIZ ATTEMPT
    # ========================================================

    def create_attempt(
        self,
        *,
        quiz_id: int,
        user_id: int,
        score: int,
        total_questions: int,
        answers: list[
            tuple[
                QuizQuestion,
                int | None,
                bool,
            ]
        ],
    ) -> tuple[
        QuizAttempt,
        list[QuizAttemptAnswer],
    ]:

        try:

            attempt = (
                QuizAttempt(
                    quiz_id=
                        quiz_id,

                    user_id=
                        user_id,

                    score=
                        score,

                    total_questions=
                        total_questions,
                )
            )


            self.db.add(
                attempt
            )


            self.db.flush()


            saved_answers: list[
                QuizAttemptAnswer
            ] = []


            for (
                question,
                selected_index,
                is_correct,
            ) in answers:

                answer = (
                    QuizAttemptAnswer(
                        attempt_id=
                            attempt.id,

                        question_id=
                            question.id,

                        selected_index=
                            selected_index,

                        is_correct=
                            is_correct,
                    )
                )


                self.db.add(
                    answer
                )


                saved_answers.append(
                    answer
                )


            self.db.commit()


            self.db.refresh(
                attempt
            )


            return (
                attempt,
                saved_answers,
            )


        except Exception:

            self.db.rollback()

            raise