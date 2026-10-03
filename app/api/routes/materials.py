from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)

from fastapi.responses import (
    FileResponse,
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

from app.schemas.material import (
    ImageMaterialTitleUpdateRequest,
    MaterialResponse,
    TextMaterialCreateRequest,
    TextMaterialUpdateRequest,
)

from app.services.material_service import (
    MaterialFileNotFoundError,
    MaterialNotFoundError,
    MaterialService,
    SubjectNotFoundError,
    UnsupportedMaterialEditError,
    UnsupportedMaterialFileError,
)

from app.services.storage_service import (
    FileTooLargeError,
    InvalidImageError,
    InvalidPdfError,
)


router = APIRouter(
    tags=[
        "Materials"
    ],
)


# =========================================================
# GET MATERIALS
# =========================================================

@router.get(
    "/api/v1/subjects/{subject_id}/materials",
    response_model=list[MaterialResponse],
)
def get_materials(
    subject_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        return service.get_materials(
            subject_id,
            current_user,
        )

    except SubjectNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Subject not found.",
        )


# =========================================================
# GET ONE MATERIAL
# =========================================================

@router.get(
    "/api/v1/materials/{material_id}",
    response_model=MaterialResponse,
)
def get_material(
    material_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        return service.get_material(
            material_id,
            current_user,
        )

    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )


# =========================================================
# GET FILE
# =========================================================

@router.get(
    "/api/v1/materials/{material_id}/file",
)
def get_material_file(
    material_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        (
            material,
            file_path,
        ) = (
            service.get_material_file(
                material_id,
                current_user,
            )
        )

        return FileResponse(
            path=file_path,

            media_type=(
                material.mime_type
                or
                "application/octet-stream"
            ),

            filename=(
                material.file_name
                or
                "material-file"
            ),
        )

    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )

    except UnsupportedMaterialFileError:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "This material does not contain a file.",
        )

    except MaterialFileNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material file not found.",
        )


# =========================================================
# CREATE TEXT
# =========================================================

@router.post(
    "/api/v1/subjects/{subject_id}/materials/text",

    response_model=
        MaterialResponse,

    status_code=
        status.HTTP_201_CREATED,
)
def create_text_material(
    subject_id: int,

    request:
        TextMaterialCreateRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        return (
            service.create_text_material(
                subject_id,
                request,
                current_user,
            )
        )

    except SubjectNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Subject not found.",
        )


# =========================================================
# CREATE PDF
# =========================================================

@router.post(
    "/api/v1/subjects/{subject_id}/materials/pdf",

    response_model=
        MaterialResponse,

    status_code=
        status.HTTP_201_CREATED,
)
async def create_pdf_material(
    subject_id: int,

    title: Annotated[
        str,
        Form(
            min_length=1,
            max_length=200,
        ),
    ],

    file: Annotated[
        UploadFile,
        File(),
    ],

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        return (
            await service
            .create_pdf_material(
                subject_id=
                    subject_id,

                title=
                    title,

                file=
                    file,

                current_user=
                    current_user,
            )
        )

    except SubjectNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Subject not found.",
        )

    except InvalidPdfError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                str(exc),
        )

    except FileTooLargeError as exc:

        raise HTTPException(
            status_code=413,

            detail=
                str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                str(exc),
        )


# =========================================================
# CREATE IMAGE
# =========================================================

@router.post(
    "/api/v1/subjects/{subject_id}/materials/image",

    response_model=
        MaterialResponse,

    status_code=
        status.HTTP_201_CREATED,
)
async def create_image_material(
    subject_id: int,

    title: Annotated[
        str,
        Form(
            min_length=1,
            max_length=200,
        ),
    ],

    file: Annotated[
        UploadFile,
        File(),
    ],

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        return (
            await service
            .create_image_material(
                subject_id=
                    subject_id,

                title=
                    title,

                file=
                    file,

                current_user=
                    current_user,
            )
        )

    except SubjectNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Subject not found.",
        )

    except InvalidImageError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                str(exc),
        )

    except FileTooLargeError as exc:

        raise HTTPException(
            status_code=413,

            detail=
                str(exc),
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                str(exc),
        )


# =========================================================
# UPDATE TEXT
# =========================================================

@router.put(
    "/api/v1/materials/{material_id}",
    response_model=MaterialResponse,
)
def update_text_material(
    material_id: int,

    request:
        TextMaterialUpdateRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        return (
            service.update_text_material(
                material_id,
                request,
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

    except UnsupportedMaterialEditError:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Only text materials can "
                "be edited using this endpoint.",
        )


# =========================================================
# UPDATE IMAGE TITLE
# =========================================================

@router.patch(
    "/api/v1/materials/{material_id}/image-title",
    response_model=MaterialResponse,
)
def update_image_title(
    material_id: int,

    request:
        ImageMaterialTitleUpdateRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        return (
            service.update_image_title(
                material_id,
                request,
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

    except UnsupportedMaterialEditError:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Only image materials "
                "can be renamed here.",
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                str(exc),
        )


# =========================================================
# DELETE
# =========================================================

@router.delete(
    "/api/v1/materials/{material_id}",

    status_code=
        status.HTTP_204_NO_CONTENT,
)
def delete_material(
    material_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = MaterialService(
        db
    )

    try:

        service.delete_material(
            material_id,
            current_user,
        )

    except MaterialNotFoundError:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Material not found.",
        )

    return Response(
        status_code=
            status.HTTP_204_NO_CONTENT
    )