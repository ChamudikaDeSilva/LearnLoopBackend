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

        # ====================================================
        # GET MATERIAL
        # ====================================================

        material = (
            material_service
            .get_material(
                material_id,
                current_user,
            )
        )


        # ====================================================
        # EXTRACT CONTENT
        # ====================================================

        extracted = (
            extraction_service
            .extract(
                material
            )
        )


        # ====================================================
        # RESPONSE
        # ====================================================

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
    # CONTENT FILE NOT FOUND
    # ========================================================

    except ContentFileNotFoundError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                str(exc),
        )


    # ========================================================
    # INVALID / UNSUPPORTED MATERIAL
    # ========================================================

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

        # ====================================================
        # MATERIAL SERVICE
        # ====================================================

        material_service = (
            MaterialService(
                db
            )
        )


        # ====================================================
        # MATERIAL AI SERVICE
        # ====================================================

        material_ai_service = (
            MaterialAIService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        # ====================================================
        # LOAD SAVED SUMMARY
        # ====================================================

        return (
            material_ai_service
            .get_saved_summary(
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
    # SUMMARY NOT FOUND
    # ========================================================

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

        # ====================================================
        # MATERIAL SERVICE
        # ====================================================

        material_service = (
            MaterialService(
                db
            )
        )


        # ====================================================
        # MATERIAL AI SERVICE
        # ====================================================

        material_ai_service = (
            MaterialAIService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        # ====================================================
        # GENERATE SUMMARY
        # ====================================================

        return (
            material_ai_service
            .generate_summary(
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
    # FILE NOT FOUND
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
    # AI PROVIDER
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

        # ====================================================
        # MATERIAL SERVICE
        # ====================================================

        material_service = (
            MaterialService(
                db
            )
        )


        # ====================================================
        # FLASHCARD SERVICE
        # ====================================================

        flashcard_service = (
            MaterialFlashcardService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        # ====================================================
        # LOAD SAVED FLASHCARDS
        # ====================================================

        return (
            flashcard_service
            .get_saved(
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
    # FLASHCARDS NOT FOUND
    # ========================================================

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

    # ========================================================
    # NUMBER OF FLASHCARDS
    #
    # Example:
    #
    # POST
    # /api/v1/ai/materials/21/flashcards?count=8
    #
    # Minimum: 4
    # Maximum: 20
    # Default: 8
    # ========================================================

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

        # ====================================================
        # MATERIAL SERVICE
        # ====================================================

        material_service = (
            MaterialService(
                db
            )
        )


        # ====================================================
        # FLASHCARD SERVICE
        # ====================================================

        flashcard_service = (
            MaterialFlashcardService(
                material_service=
                    material_service,

                db=
                    db,
            )
        )


        # ====================================================
        # GENERATE / REGENERATE
        # ====================================================

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
    # FILE NOT FOUND
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
    # AI PROVIDER FAILURE
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