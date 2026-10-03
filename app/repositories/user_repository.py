from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def get_by_id(
        self,
        user_id: int,
    ) -> User | None:

        return self.db.get(
            User,
            user_id,
        )

    def get_by_email(
        self,
        email: str,
    ) -> User | None:

        statement = select(
            User
        ).where(
            User.email == email
        )

        return self.db.scalar(
            statement
        )

    def create(
        self,
        name: str,
        email: str,
        password_hash: str,
    ) -> User:

        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
        )

        self.db.add(
            user
        )

        try:
            self.db.commit()

            self.db.refresh(
                user
            )

            return user

        except IntegrityError:
            self.db.rollback()
            raise