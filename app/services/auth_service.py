from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import (
    UserRepository,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
)


class EmailAlreadyRegisteredError(
    Exception
):
    pass


class InvalidCredentialsError(
    Exception
):
    pass


class AuthService:

    def __init__(
        self,
        db: Session,
    ):
        self.user_repository = (
            UserRepository(db)
        )

    def register(
        self,
        request: RegisterRequest,
    ) -> User:

        email = (
            request.email
            .strip()
            .lower()
        )

        name = request.name.strip()

        existing_user = (
            self.user_repository
            .get_by_email(email)
        )

        if existing_user:
            raise (
                EmailAlreadyRegisteredError()
            )

        hashed_password = (
            hash_password(
                request.password
            )
        )

        try:
            return (
                self.user_repository.create(
                    name=name,
                    email=email,
                    password_hash=(
                        hashed_password
                    ),
                )
            )

        except IntegrityError as exc:
            raise (
                EmailAlreadyRegisteredError()
            ) from exc

    def login(
        self,
        request: LoginRequest,
    ) -> tuple[User, str]:

        email = (
            request.email
            .strip()
            .lower()
        )

        user = (
            self.user_repository
            .get_by_email(email)
        )

        if user is None:
            raise InvalidCredentialsError()

        password_is_valid = (
            verify_password(
                request.password,
                user.password_hash,
            )
        )

        if not password_is_valid:
            raise InvalidCredentialsError()

        access_token = (
            create_access_token(
                user.id
            )
        )

        return (
            user,
            access_token,
        )