from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
)
from app.core.database import get_db
from app.models.user import User
from app.schemas.subject import (
    SubjectCreateRequest,
    SubjectResponse,
    SubjectUpdateRequest,
)
from app.services.subject_service import (
    SubjectNotFoundError,
    SubjectService,
)


router = APIRouter(
    prefix="/api/v1/subjects",
    tags=["Subjects"],
)


@router.get(
    "",
    response_model=list[SubjectResponse],
)
def get_subjects(
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = SubjectService(
        db
    )

    return service.get_subjects(
        current_user
    )


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def get_subject(
    subject_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = SubjectService(
        db
    )

    try:
        return service.get_subject(
            subject_id,
            current_user,
        )

    except SubjectNotFoundError:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Subject not found.",
        )


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    request: SubjectCreateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = SubjectService(
        db
    )

    return service.create_subject(
        request,
        current_user,
    )


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def update_subject(
    subject_id: int,
    request: SubjectUpdateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = SubjectService(
        db
    )

    try:
        return service.update_subject(
            subject_id,
            request,
            current_user,
        )

    except SubjectNotFoundError:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Subject not found.",
        )


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_subject(
    subject_id: int,
    current_user: User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    service = SubjectService(
        db
    )

    try:
        service.delete_subject(
            subject_id,
            current_user,
        )

    except SubjectNotFoundError:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Subject not found.",
        )

    return Response(
        status_code=(
            status.HTTP_204_NO_CONTENT
        )
    )