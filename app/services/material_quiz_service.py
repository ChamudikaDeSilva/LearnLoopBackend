from sqlalchemy.orm import (
    Session,
)

from app.models.material import (
    Material,
)

from app.models.material_quiz import (
    MaterialQuiz,
)

from app.models.quiz_question import (
    QuizQuestion,
)

from app.models.user import (
    User,
)

from app.repositories.quiz_repository import (
    QuizRepository,
)

from app.schemas.quiz import (
    MaterialQuizResponse,
    QuizAnswerResult,
    QuizGenerationContent,
    QuizQuestionResponse,
    QuizSubmissionRequest,
    QuizSubmissionResponse,
)

from app.services.ai_service import (
    AIService,
)

from app.services.content_extraction_service import (
    ContentExtractionService,
    UnsupportedContentTypeError,
)

from app.services.material_service import (
    MaterialService,
)


# ============================================================
# CONSTANTS
# ============================================================


DEFAULT_QUIZ_QUESTION_COUNT = 10


# ============================================================
# EXCEPTIONS
# ============================================================


class QuizNotFoundError(
    Exception
):
    pass


class MaterialQuizNotFoundError(
    Exception
):
    pass


class QuizSubmissionError(
    Exception
):
    pass


# ============================================================
# MATERIAL QUIZ SERVICE
# ============================================================


class MaterialQuizService:

    # ========================================================
    # CONSTRUCTOR
    # ========================================================

    def __init__(
        self,
        material_service:
            MaterialService,
        db:
            Session,
        ai_service:
            AIService | None = None,
    ):

        self.material_service = (
            material_service
        )

        self.extraction_service = (
            ContentExtractionService()
        )

        self.ai_service = (
            ai_service
            or
            AIService()
        )

        self.quiz_repository = (
            QuizRepository(
                db
            )
        )


    # ========================================================
    # QUIZ RESPONSE
    #
    # IMPORTANT:
    #
    # correct_index is NOT sent to mobile.
    # explanation is NOT sent to mobile.
    #
    # They become available only after submission.
    # ========================================================

    def _to_quiz_response(
        self,
        material:
            Material,
        quiz:
            MaterialQuiz,
        questions:
            list[
                QuizQuestion
            ],
    ) -> MaterialQuizResponse:

        return (
            MaterialQuizResponse(
                quiz_id=
                    quiz.id,

                material_id=
                    material.id,

                title=
                    material.title,

                source_type=
                    material.source_type,

                provider=
                    quiz.provider,

                question_count=
                    len(
                        questions
                    ),

                questions=[
                    QuizQuestionResponse(
                        id=
                            question.id,

                        position=
                            question.position,

                        question=
                            question.question,

                        options=
                            question.options,
                    )
                    for question
                    in questions
                ],
            )
        )


    # ========================================================
    # SAVE GENERATED QUIZ
    # ========================================================

    def _save_generated_quiz(
        self,
        material:
            Material,
        generated:
            QuizGenerationContent,
    ) -> MaterialQuizResponse:

        if not generated.questions:

            raise ValueError(
                "No quiz questions "
                "were generated."
            )


        (
            quiz,
            questions,
        ) = (
            self.quiz_repository
            .create_quiz(
                material_id=
                    material.id,

                provider=
                    self.ai_service
                    .provider_name,

                generated=
                    generated,
            )
        )


        return (
            self._to_quiz_response(
                material=
                    material,

                quiz=
                    quiz,

                questions=
                    questions,
            )
        )


    # ========================================================
    # GENERATE QUIZ FROM TEXT / PDF
    # ========================================================

    def _generate_from_text(
        self,
        material:
            Material,
        question_count:
            int,
    ) -> MaterialQuizResponse:

        # ====================================================
        # EXTRACT STUDY CONTENT
        # ====================================================

        extracted = (
            self.extraction_service
            .extract(
                material
            )
        )


        # ====================================================
        # GENERATE QUESTIONS
        # ====================================================

        generated = (
            self.ai_service
            .generate_quiz(
                text=
                    extracted.text,

                question_count=
                    question_count,
            )
        )


        # ====================================================
        # SAVE
        # ====================================================

        return (
            self._save_generated_quiz(
                material=
                    material,

                generated=
                    generated,
            )
        )


    # ========================================================
    # GENERATE QUIZ FROM IMAGE / CAMERA
    # ========================================================

    def _generate_from_image(
        self,
        material:
            Material,
        current_user:
            User,
        question_count:
            int,
    ) -> MaterialQuizResponse:

        # ====================================================
        # GET PRIVATE MATERIAL FILE
        # ====================================================

        (
            _,
            file_path,
        ) = (
            self.material_service
            .get_material_file(
                material.id,
                current_user,
            )
        )


        # ====================================================
        # MIME TYPE
        # ====================================================

        mime_type = (
            material.mime_type
            or
            "image/jpeg"
        )


        # ====================================================
        # GENERATE QUIZ DIRECTLY FROM IMAGE
        # ====================================================

        generated = (
            self.ai_service
            .generate_quiz_from_image(
                file_path=
                    file_path,

                mime_type=
                    mime_type,

                question_count=
                    question_count,
            )
        )


        # ====================================================
        # SAVE
        # ====================================================

        return (
            self._save_generated_quiz(
                material=
                    material,

                generated=
                    generated,
            )
        )


    # ========================================================
    # GENERATE NEW QUIZ
    #
    # Every call creates a NEW quiz version.
    #
    # Previous quiz attempts remain linked to the exact
    # questions that were answered.
    # ========================================================

    def generate(
        self,
        material_id:
            int,
        current_user:
            User,
        question_count:
            int =
            DEFAULT_QUIZ_QUESTION_COUNT,
    ) -> MaterialQuizResponse:

        # ====================================================
        # GET MATERIAL + VERIFY OWNERSHIP
        # ====================================================

        material = (
            self.material_service
            .get_material(
                material_id,
                current_user,
            )
        )


        # ====================================================
        # TEXT / PDF
        # ====================================================

        if (
            material.source_type
            in (
                "text",
                "pdf",
            )
        ):

            return (
                self._generate_from_text(
                    material=
                        material,

                    question_count=
                        question_count,
                )
            )


        # ====================================================
        # IMAGE / CAMERA
        # ====================================================

        if (
            material.source_type
            in (
                "image",
                "camera",
            )
        ):

            return (
                self._generate_from_image(
                    material=
                        material,

                    current_user=
                        current_user,

                    question_count=
                        question_count,
                )
            )


        # ====================================================
        # UNSUPPORTED SOURCE
        # ====================================================

        raise UnsupportedContentTypeError(
            "Unsupported material source type: "
            f"{material.source_type}"
        )


    # ========================================================
    # GET LATEST SAVED QUIZ
    # ========================================================

    def get_latest(
        self,
        material_id:
            int,
        current_user:
            User,
    ) -> MaterialQuizResponse:

        # ====================================================
        # GET MATERIAL + VERIFY OWNERSHIP
        # ====================================================

        material = (
            self.material_service
            .get_material(
                material_id,
                current_user,
            )
        )


        # ====================================================
        # GET LATEST QUIZ
        # ====================================================

        quiz = (
            self.quiz_repository
            .get_latest_by_material_id(
                material.id
            )
        )


        if quiz is None:

            raise (
                MaterialQuizNotFoundError()
            )


        # ====================================================
        # GET QUESTIONS
        # ====================================================

        questions = (
            self.quiz_repository
            .get_questions(
                quiz.id
            )
        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return (
            self._to_quiz_response(
                material=
                    material,

                quiz=
                    quiz,

                questions=
                    questions,
            )
        )


    # ========================================================
    # SUBMIT QUIZ
    # ========================================================

    def submit(
        self,
        quiz_id:
            int,
        current_user:
            User,
        submission:
            QuizSubmissionRequest,
    ) -> QuizSubmissionResponse:

        # ====================================================
        # GET QUIZ
        # ====================================================

        quiz = (
            self.quiz_repository
            .get_by_id(
                quiz_id
            )
        )


        if quiz is None:

            raise (
                QuizNotFoundError()
            )


        # ====================================================
        # OWNERSHIP VALIDATION
        #
        # This is the section that caused your syntax error.
        #
        # Keeping the chained method call inside parentheses
        # makes the multiline syntax valid.
        # ====================================================

        (
            self.material_service
            .get_material(
                quiz.material_id,
                current_user,
            )
        )


        # ====================================================
        # LOAD QUIZ QUESTIONS
        # ====================================================

        questions = (
            self.quiz_repository
            .get_questions(
                quiz.id
            )
        )


        if not questions:

            raise QuizSubmissionError(
                "This quiz contains "
                "no questions."
            )


        # ====================================================
        # QUESTION LOOKUP
        # ====================================================

        question_map = {
            question.id:
                question
            for question
            in questions
        }


        # ====================================================
        # VALIDATE SUBMITTED QUESTION IDs
        #
        # Prevent submitting answers belonging to another quiz.
        # ====================================================

        for answer in (
            submission.answers
        ):

            if (
                answer.question_id
                not in
                question_map
            ):

                raise QuizSubmissionError(
                    "The submission contains "
                    "a question that does not "
                    "belong to this quiz."
                )


        # ====================================================
        # USER ANSWER LOOKUP
        #
        # Example:
        #
        # {
        #     21: 0,
        #     22: 2,
        #     23: None
        # }
        # ====================================================

        submitted_map = {
            answer.question_id:
                answer.selected_index
            for answer
            in submission.answers
        }


        # ====================================================
        # VALUES FOR DATABASE PERSISTENCE
        # ====================================================

        scored_answers: list[
            tuple[
                QuizQuestion,
                int | None,
                bool,
            ]
        ] = []


        # ====================================================
        # VALUES FOR RESULT SCREEN
        # ====================================================

        result_items: list[
            QuizAnswerResult
        ] = []


        score = 0


        # ====================================================
        # SCORE EVERY QUESTION
        #
        # Missing answers:
        #
        # selected_index = None
        # is_correct = False
        # ====================================================

        for question in questions:

            selected_index = (
                submitted_map.get(
                    question.id
                )
            )


            is_correct = (
                selected_index
                is not None
                and
                selected_index
                ==
                question.correct_index
            )


            # =================================================
            # SCORE
            # =================================================

            if is_correct:

                score += 1


            # =================================================
            # SAVE ATTEMPT ANSWER
            # =================================================

            scored_answers.append(
                (
                    question,
                    selected_index,
                    is_correct,
                )
            )


            # =================================================
            # RESULT REVIEW ITEM
            #
            # correct_index and explanation are exposed
            # only after quiz submission.
            # =================================================

            result_items.append(
                QuizAnswerResult(
                    question_id=
                        question.id,

                    position=
                        question.position,

                    question=
                        question.question,

                    options=
                        question.options,

                    selected_index=
                        selected_index,

                    correct_index=
                        question.correct_index,

                    is_correct=
                        is_correct,

                    explanation=
                        question.explanation,
                )
            )


        # ====================================================
        # SAVE ATTEMPT
        # ====================================================

        (
            attempt,
            _,
        ) = (
            self.quiz_repository
            .create_attempt(
                quiz_id=
                    quiz.id,

                user_id=
                    current_user.id,

                score=
                    score,

                total_questions=
                    len(
                        questions
                    ),

                answers=
                    scored_answers,
            )
        )


        # ====================================================
        # RESULT CALCULATION
        # ====================================================

        total_questions = (
            len(
                questions
            )
        )


        percentage = (
            (
                score
                /
                total_questions
            )
            *
            100
        )


        # ====================================================
        # RESULT RESPONSE
        # ====================================================

        return (
            QuizSubmissionResponse(
                attempt_id=
                    attempt.id,

                quiz_id=
                    quiz.id,

                score=
                    score,

                total_questions=
                    total_questions,

                percentage=
                    round(
                        percentage,
                        2,
                    ),

                answers=
                    result_items,
            )
        )