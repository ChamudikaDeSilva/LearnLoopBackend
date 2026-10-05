from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import (
    Session,
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
)

from app.services.content_extraction_service import (
    ContentExtractionError,
    ContentExtractionService,
    ContentFileNotFoundError,
    EmptyMaterialContentError,
    UnsupportedContentTypeError,
)

from app.services.material_service import (
    MaterialNotFoundError,
    MaterialService,
)


router = APIRouter(
    prefix="/api/v1/ai",
    tags=[
        "AI"
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

        # ----------------------------------------------------
        # IMPORTANT
        #
        # This method already validates that the
        # material belongs to the logged-in user.
        # ----------------------------------------------------

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


        return (
            MaterialExtractionResponse(
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


    except EmptyMaterialContentError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                str(exc),
        )


    except UnsupportedContentTypeError as exc:

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