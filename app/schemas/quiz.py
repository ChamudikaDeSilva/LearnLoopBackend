from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


# ============================================================
# GEMINI GENERATED QUESTION
# ============================================================


class QuizQuestionContent(
    BaseModel
):

    question: str = Field(
        min_length=1,
        description=(
            "A clear multiple-choice question "
            "based only on the study material."
        ),
    )


    options: list[str] = Field(
        min_length=4,
        max_length=4,
        description=(
            "Exactly four distinct answer options."
        ),
    )


    correct_index: int = Field(
        ge=0,
        le=3,
        description=(
            "Zero-based index of the correct option."
        ),
    )


    explanation: str = Field(
        min_length=1,
        description=(
            "A concise explanation of why "
            "the correct answer is correct."
        ),
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    @model_validator(
        mode="after"
    )
    def validate_question(
        self,
    ):

        self.question = (
            self.question.strip()
        )


        self.explanation = (
            self.explanation.strip()
        )


        cleaned_options = [
            option.strip()
            for option
            in self.options
        ]


        if any(
            not option
            for option
            in cleaned_options
        ):

            raise ValueError(
                "Quiz options cannot be empty."
            )


        normalized_options = [
            option.lower()
            for option
            in cleaned_options
        ]


        if (
            len(
                set(
                    normalized_options
                )
            )
            !=
            4
        ):

            raise ValueError(
                "Quiz options must be distinct."
            )


        self.options = (
            cleaned_options
        )


        return self


# ============================================================
# GEMINI STRUCTURED OUTPUT
# ============================================================


class QuizGenerationContent(
    BaseModel
):

    questions: list[
        QuizQuestionContent
    ] = Field(
        min_length=1,
        description=(
            "Generated multiple-choice "
            "quiz questions."
        ),
    )


# ============================================================
# MOBILE QUESTION RESPONSE
#
# IMPORTANT:
# correct_index is intentionally NOT exposed here.
# ============================================================


class QuizQuestionResponse(
    BaseModel
):

    id: int

    position: int

    question: str

    options: list[str]


# ============================================================
# MOBILE QUIZ RESPONSE
# ============================================================


class MaterialQuizResponse(
    BaseModel
):

    quiz_id: int

    material_id: int

    title: str

    source_type: str

    provider: str

    question_count: int

    questions: list[
        QuizQuestionResponse
    ]


# ============================================================
# ONE SUBMITTED ANSWER
# ============================================================


class QuizAnswerSubmission(
    BaseModel
):

    question_id: int

    selected_index: (
        int | None
    ) = Field(
        default=None,
        ge=0,
        le=3,
    )


# ============================================================
# SUBMIT QUIZ REQUEST
# ============================================================


class QuizSubmissionRequest(
    BaseModel
):

    answers: list[
        QuizAnswerSubmission
    ]


    @model_validator(
        mode="after"
    )
    def validate_answers(
        self,
    ):

        question_ids = [
            answer.question_id
            for answer
            in self.answers
        ]


        if (
            len(
                question_ids
            )
            !=
            len(
                set(
                    question_ids
                )
            )
        ):

            raise ValueError(
                "A quiz question cannot "
                "be submitted more than once."
            )


        return self


# ============================================================
# RESULT REVIEW ITEM
#
# Correct answer becomes visible only after submission.
# ============================================================


class QuizAnswerResult(
    BaseModel
):

    question_id: int

    position: int

    question: str

    options: list[str]

    selected_index: (
        int | None
    )

    correct_index: int

    is_correct: bool

    explanation: str


# ============================================================
# QUIZ RESULT RESPONSE
# ============================================================


class QuizSubmissionResponse(
    BaseModel
):

    attempt_id: int

    quiz_id: int

    score: int

    total_questions: int

    percentage: float

    answers: list[
        QuizAnswerResult
    ]