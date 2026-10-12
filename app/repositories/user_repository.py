from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class ConcurrentAccountUpdateError(Exception):
    pass


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

    def get_by_id_for_update(self, user_id: int) -> User | None:
        # Reload an identity that may already have been read by bearer authentication.
        statement = (
            select(User)
            .where(User.id == user_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self.db.scalar(statement)

    def update_account(
        self,
        user: User,
        expected_auth_version: int,
        **changes,
    ) -> User:
        # The version condition also protects databases without row-level SELECT locks.
        statement = (
            update(User)
            .where(User.id == user.id, User.auth_version == expected_auth_version)
            .values(**changes, updated_at=func.now())
            .execution_options(synchronize_session=False)
        )
        result = self.db.execute(statement)
        if result.rowcount != 1:
            raise ConcurrentAccountUpdateError()
        self.db.commit()
        self.db.refresh(user)
        return user

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
