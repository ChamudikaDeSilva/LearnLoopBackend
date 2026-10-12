from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import (
    ConcurrentAccountUpdateError,
    UserRepository,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UpdateProfileRequest,
    ChangePasswordRequest,
)


class EmailAlreadyRegisteredError(
    Exception
):
    pass


class InvalidCredentialsError(
    Exception
):
    pass


class IncorrectCurrentPasswordError(Exception):
    pass


class UnchangedPasswordError(Exception):
    pass


class StaleAuthenticationError(Exception):
    pass


class AuthService:

    def __init__(
        self,
        db: Session,
    ):
        self.db = db
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
                user.id,
                user.auth_version,
            )
        )

        return (
            user,
            access_token,
        )

    def _lock_authenticated_user(self, user_id: int, expected_auth_version: int) -> User:
        user = self.user_repository.get_by_id_for_update(user_id)
        if user is None or user.auth_version != expected_auth_version:
            raise StaleAuthenticationError()
        return user

    def update_profile(
        self,
        user_id: int,
        expected_auth_version: int,
        request: UpdateProfileRequest,
    ) -> tuple[User, str]:
        try:
            user = self._lock_authenticated_user(user_id, expected_auth_version)
            email = str(request.email).strip().lower()
            email_changed = email != user.email.strip().lower()
            if email_changed:
                if request.current_password is None or not verify_password(
                    request.current_password, user.password_hash
                ):
                    raise IncorrectCurrentPasswordError()
                existing = self.user_repository.get_by_email(email)
                if existing is not None and existing.id != user.id:
                    raise EmailAlreadyRegisteredError()

            version = user.auth_version + int(email_changed)
            token = create_access_token(user.id, version)
            updated_user = self.user_repository.update_account(
                user,
                expected_auth_version,
                name=request.name.strip(),
                email=email,
                auth_version=version,
            )
            return updated_user, token
        except IntegrityError as exc:
            self.db.rollback()
            raise EmailAlreadyRegisteredError() from exc
        except ConcurrentAccountUpdateError as exc:
            self.db.rollback()
            raise StaleAuthenticationError() from exc
        except Exception:
            self.db.rollback()
            raise

    def change_password(
        self,
        user_id: int,
        expected_auth_version: int,
        request: ChangePasswordRequest,
    ) -> tuple[User, str]:
        try:
            user = self._lock_authenticated_user(user_id, expected_auth_version)
            if not verify_password(request.current_password, user.password_hash):
                raise IncorrectCurrentPasswordError()
            if request.new_password == request.current_password:
                raise UnchangedPasswordError()

            version = user.auth_version + 1
            token = create_access_token(user.id, version)
            updated_user = self.user_repository.update_account(
                user,
                expected_auth_version,
                password_hash=hash_password(request.new_password),
                auth_version=version,
            )
            return updated_user, token
        except ConcurrentAccountUpdateError as exc:
            self.db.rollback()
            raise StaleAuthenticationError() from exc
        except Exception:
            self.db.rollback()
            raise
