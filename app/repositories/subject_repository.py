from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subject import Subject


class SubjectRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db


    def get_all_by_user(
        self,
        user_id: int,
    ) -> list[Subject]:

        statement = (
            select(Subject)
            .where(
                Subject.user_id == user_id
            )
            .order_by(
                Subject.created_at.desc()
            )
        )

        return list(
            self.db.scalars(
                statement
            ).all()
        )


    def get_by_id_and_user(
        self,
        subject_id: int,
        user_id: int,
    ) -> Subject | None:

        statement = (
            select(Subject)
            .where(
                Subject.id == subject_id,
                Subject.user_id == user_id,
            )
        )

        return self.db.scalar(
            statement
        )


    def create(
        self,
        user_id: int,
        name: str,
        description: str | None,
    ) -> Subject:

        subject = Subject(
            user_id=user_id,
            name=name,
            description=description,
        )

        self.db.add(
            subject
        )

        self.db.commit()

        self.db.refresh(
            subject
        )

        return subject


    def update(
        self,
        subject: Subject,
        name: str,
        description: str | None,
    ) -> Subject:

        subject.name = name
        subject.description = description

        self.db.commit()

        self.db.refresh(
            subject
        )

        return subject


    def delete(
        self,
        subject: Subject,
    ) -> None:

        self.db.delete(
            subject
        )

        self.db.commit()