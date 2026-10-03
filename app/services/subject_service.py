from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.user import User
from app.repositories.subject_repository import (
    SubjectRepository,
)
from app.schemas.subject import (
    SubjectCreateRequest,
    SubjectUpdateRequest,
)


class SubjectNotFoundError(
    Exception
):
    pass


class SubjectService:

    def __init__(
        self,
        db: Session,
    ):
        self.subject_repository = (
            SubjectRepository(db)
        )


    def get_subjects(
        self,
        current_user: User,
    ) -> list[Subject]:

        return (
            self.subject_repository
            .get_all_by_user(
                current_user.id
            )
        )


    def get_subject(
        self,
        subject_id: int,
        current_user: User,
    ) -> Subject:

        subject = (
            self.subject_repository
            .get_by_id_and_user(
                subject_id,
                current_user.id,
            )
        )

        if subject is None:
            raise SubjectNotFoundError()

        return subject


    def create_subject(
        self,
        request: SubjectCreateRequest,
        current_user: User,
    ) -> Subject:

        name = request.name.strip()

        description = (
            request.description.strip()
            if request.description
            else None
        )

        return (
            self.subject_repository.create(
                user_id=current_user.id,
                name=name,
                description=description,
            )
        )


    def update_subject(
        self,
        subject_id: int,
        request: SubjectUpdateRequest,
        current_user: User,
    ) -> Subject:

        subject = self.get_subject(
            subject_id,
            current_user,
        )

        name = request.name.strip()

        description = (
            request.description.strip()
            if request.description
            else None
        )

        return (
            self.subject_repository.update(
                subject=subject,
                name=name,
                description=description,
            )
        )


    def delete_subject(
        self,
        subject_id: int,
        current_user: User,
    ) -> None:

        subject = self.get_subject(
            subject_id,
            current_user,
        )

        self.subject_repository.delete(
            subject
        )