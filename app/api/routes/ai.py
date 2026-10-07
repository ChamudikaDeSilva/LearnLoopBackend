from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy.orm import (
    Session,
)

from app.ai.providers.base import (
    AIConfigurationError,
    AIProviderError,
)

from app.api.dependencies import (
    get_current_user,
)

from app.core.database import (
    get_db,
)

from app.models.user import (
    User,
)

from app.schemas.ai import (
    MaterialExtractionResponse,
    MaterialSummaryResponse,
)

from app.schemas.flashcard import (
    MaterialFlashcardsResponse,
)

from app.schemas.quiz import (
    MaterialQuizResponse,
    QuizSubmissionRequest,
    QuizSubmissionResponse,
)

from app.services.content_extraction_service import (
    ContentExtractionError,
    ContentExtractionService,
    ContentFileNotFoundError,
    EmptyMaterialContentError,
    UnsupportedContentTypeError,
)

from app.services.material_ai_service import (
    MaterialAIService,
    MaterialSummaryNotFoundError,
)

from app.services.material_flashcard_service import (
    FlashcardSetNotFoundError,
    MaterialFlashcardService,
)

from app.services.material_quiz_service import (
    MaterialQuizNotFoundError,
    MaterialQuizService,
    QuizNotFoundError,
    QuizSubmissionError,
)

from app.services.material_service import (
    MaterialFileNotFoundError,
    MaterialNotFoundError,
    MaterialService,
    UnsupportedMaterialFileError,
)


# ============================================================
# ROUTER
# ============================================================


router = APIRouter(
    prefix="/api/v1/ai",
    tags=[
        "AI",
    ],
)


# ============================================================
# EXTRACT MATERIAL CONTENT
# ============================================================


@router.get(
    "/materials/{material_id}/extract",
    response_model=
        MaterialExtractionResponse,
)
def extract_material_content(
    material_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    material_service = (
        MaterialService(
            db
        )
    )


    extraction_service = (
        ContentExtractionService()
    )


    try:

        material = (
            material_service
            .get_material(
                material_id,
                current_user,
            )
        )


        extracted = (
            extraction_service
            .extract(
                material
            )
        )


        return MaterialExtractionResponse(
            material_id=
                material.id,

            title=
                material.title,

            source_type=
                material.source_type,

            text=
                extracted.text,

            character_count=
                extracted.character_count,
        )


    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


    except ContentFileNotFoundError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                str(exc),
        )


    except (
        EmptyMaterialContentError,
        UnsupportedContentTypeError,
    ) as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc),
        )


    except ContentExtractionError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                str(exc),
        )


# ============================================================
# GET SAVED MATERIAL SUMMARY
# ============================================================


@router.get(
    "/materials/{material_id}/summary",
    response_model=
        MaterialSummaryResponse,
)
def get_material_summary(
    material_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    try:

        material_service = (
            MaterialService(
                db
            )
        )


        material_ai_service = (
            MaterialAIService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        return (
            material_ai_service
            .get_saved_summary(
                material_id=
                    material_id,

                current_user=
                    current_user,
            )
        )


    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


    except MaterialSummaryNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "No saved summary exists "
                "for this material.",
        )


# ============================================================
# GENERATE / REGENERATE MATERIAL SUMMARY
# ============================================================


@router.post(
    "/materials/{material_id}/summary",
    response_model=
        MaterialSummaryResponse,
)
def generate_material_summary(
    material_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    try:

        material_service = (
            MaterialService(
                db
            )
        )


        material_ai_service = (
            MaterialAIService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        return (
            material_ai_service
            .generate_summary(
                material_id=
                    material_id,

                current_user=
                    current_user,
            )
        )


    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


    except (
        ContentFileNotFoundError,
        MaterialFileNotFoundError,
    ) as exc:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                str(exc)
                or
                "Material file was not found.",
        )


    except (
        EmptyMaterialContentError,
        UnsupportedContentTypeError,
        UnsupportedMaterialFileError,
    ) as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc)
                or
                "The material cannot be processed.",
        )


    except AIConfigurationError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_503_SERVICE_UNAVAILABLE,

            detail=
                str(exc),
        )


    except AIProviderError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_502_BAD_GATEWAY,

            detail=
                str(exc),
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc),
        )


# ============================================================
# GET SAVED MATERIAL FLASHCARDS
# ============================================================


@router.get(
    "/materials/{material_id}/flashcards",
    response_model=
        MaterialFlashcardsResponse,
)
def get_material_flashcards(
    material_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    try:

        material_service = (
            MaterialService(
                db
            )
        )


        flashcard_service = (
            MaterialFlashcardService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        return (
            flashcard_service
            .get_saved(
                material_id=
                    material_id,

                current_user=
                    current_user,
            )
        )


    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


    except FlashcardSetNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "No saved flashcards exist "
                "for this material.",
        )


# ============================================================
# GENERATE / REGENERATE MATERIAL FLASHCARDS
# ============================================================


@router.post(
    "/materials/{material_id}/flashcards",
    response_model=
        MaterialFlashcardsResponse,
)
def generate_material_flashcards(
    material_id: int,

    count: int = Query(
        default=8,
        ge=4,
        le=20,
    ),

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    try:

        material_service = (
            MaterialService(
                db
            )
        )


        flashcard_service = (
            MaterialFlashcardService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        return (
            flashcard_service
            .generate(
                material_id=
                    material_id,

                current_user=
                    current_user,

                card_count=
                    count,
            )
        )


    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


    except (
        ContentFileNotFoundError,
        MaterialFileNotFoundError,
    ) as exc:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                str(exc)
                or
                "Material file was not found.",
        )


    except (
        EmptyMaterialContentError,
        UnsupportedContentTypeError,
        UnsupportedMaterialFileError,
    ) as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc)
                or
                "The material cannot be processed.",
        )


    except AIConfigurationError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_503_SERVICE_UNAVAILABLE,

            detail=
                str(exc),
        )


    except AIProviderError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_502_BAD_GATEWAY,

            detail=
                str(exc),
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc),
        )


# ============================================================
# GET LATEST SAVED MATERIAL QUIZ
#
# Returns the newest quiz generated for this material.
#
# IMPORTANT:
# correct_index and explanation are NOT included.
# ============================================================


@router.get(
    "/materials/{material_id}/quiz",
    response_model=
        MaterialQuizResponse,
)
def get_material_quiz(
    material_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    try:

        # ====================================================
        # MATERIAL SERVICE
        # ====================================================

        material_service = (
            MaterialService(
                db
            )
        )


        # ====================================================
        # QUIZ SERVICE
        # ====================================================

        quiz_service = (
            MaterialQuizService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        # ====================================================
        # LOAD LATEST QUIZ
        # ====================================================

        return (
            quiz_service
            .get_latest(
                material_id=
                    material_id,

                current_user=
                    current_user,
            )
        )


    # ========================================================
    # MATERIAL NOT FOUND
    # ========================================================

    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


    # ========================================================
    # NO SAVED QUIZ
    # ========================================================

    except MaterialQuizNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "No saved quiz exists "
                "for this material.",
        )


# ============================================================
# GENERATE NEW MATERIAL QUIZ
#
# IMPORTANT:
#
# Unlike Flashcards, this creates a NEW quiz version.
#
# Example:
#
# POST /api/v1/ai/materials/12/quiz?count=10
# ============================================================


@router.post(
    "/materials/{material_id}/quiz",
    response_model=
        MaterialQuizResponse,
)
def generate_material_quiz(
    material_id: int,

    count: int = Query(
        default=10,
        ge=5,
        le=20,
    ),

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    try:

        # ====================================================
        # MATERIAL SERVICE
        # ====================================================

        material_service = (
            MaterialService(
                db
            )
        )


        # ====================================================
        # QUIZ SERVICE
        # ====================================================

        quiz_service = (
            MaterialQuizService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        # ====================================================
        # GENERATE NEW QUIZ VERSION
        # ====================================================

        return (
            quiz_service
            .generate(
                material_id=
                    material_id,

                current_user=
                    current_user,

                question_count=
                    count,
            )
        )


    # ========================================================
    # MATERIAL NOT FOUND
    # ========================================================

    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


    # ========================================================
    # MATERIAL FILE NOT FOUND
    # ========================================================

    except (
        ContentFileNotFoundError,
        MaterialFileNotFoundError,
    ) as exc:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                str(exc)
                or
                "Material file was not found.",
        )


    # ========================================================
    # MATERIAL CANNOT BE PROCESSED
    # ========================================================

    except (
        EmptyMaterialContentError,
        UnsupportedContentTypeError,
        UnsupportedMaterialFileError,
    ) as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc)
                or
                "The material cannot be processed.",
        )


    # ========================================================
    # EXTRACTION FAILURE
    # ========================================================

    except ContentExtractionError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                str(exc),
        )


    # ========================================================
    # AI CONFIGURATION
    # ========================================================

    except AIConfigurationError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_503_SERVICE_UNAVAILABLE,

            detail=
                str(exc),
        )


    # ========================================================
    # GEMINI / AI FAILURE
    # ========================================================

    except AIProviderError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_502_BAD_GATEWAY,

            detail=
                str(exc),
        )


    # ========================================================
    # VALIDATION
    # ========================================================

    except ValueError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc),
        )


# ============================================================
# SUBMIT QUIZ
#
# Example body:
#
# {
#   "answers": [
#       {
#           "question_id": 1,
#           "selected_index": 2
#       },
#       {
#           "question_id": 2,
#           "selected_index": 0
#       }
#   ]
# }
#
# The backend:
#
# 1. validates quiz ownership
# 2. checks the answers
# 3. calculates score
# 4. stores quiz_attempt
# 5. stores quiz_attempt_answers
# 6. returns correct answers + explanations
# ============================================================


@router.post(
    "/quizzes/{quiz_id}/submit",
    response_model=
        QuizSubmissionResponse,
)
def submit_material_quiz(
    quiz_id: int,

    submission:
        QuizSubmissionRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    try:

        # ====================================================
        # MATERIAL SERVICE
        # ====================================================

        material_service = (
            MaterialService(
                db
            )
        )


        # ====================================================
        # QUIZ SERVICE
        # ====================================================

        quiz_service = (
            MaterialQuizService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        # ====================================================
        # SUBMIT + SCORE
        # ====================================================

        return (
            quiz_service
            .submit(
                quiz_id=
                    quiz_id,

                current_user=
                    current_user,

                submission=
                    submission,
            )
        )


    # ========================================================
    # QUIZ NOT FOUND
    # ========================================================

    except QuizNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Quiz not found.",
        )


    # ========================================================
    # MATERIAL / OWNERSHIP NOT FOUND
    # ========================================================

    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


    # ========================================================
    # INVALID SUBMISSION
    # ========================================================

    except QuizSubmissionError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc),
        )


    # ========================================================
    # VALIDATION
    # ========================================================

    except ValueError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc),
        )