import jwt

from fastapi import (
    Depends,
    HTTPException,
    status,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    decode_access_token,
)
from app.models.user import User
from app.repositories.user_repository import (
    UserRepository,
)


bearer_scheme = HTTPBearer(
    auto_error=False,
)


def get_current_user(
    credentials:
        HTTPAuthorizationCredentials
        | None
        = Depends(bearer_scheme),

    db: Session = Depends(get_db),
) -> User:

    authentication_error = HTTPException(
        status_code=(
            status.HTTP_401_UNAUTHORIZED
        ),
        detail=(
            "Authentication credentials "
            "are invalid or expired."
        ),
        headers={
            "WWW-Authenticate": "Bearer"
        },
    )

    if credentials is None:
        raise authentication_error

    if (
        credentials.scheme.lower()
        != "bearer"
    ):
        raise authentication_error

    try:
        payload = decode_access_token(
            credentials.credentials
        )

        user_id_value = payload.get(
            "sub"
        )

        if user_id_value is None:
            raise authentication_error

        user_id = int(
            user_id_value
        )

    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ):
        raise authentication_error

    repository = UserRepository(
        db
    )

    user = repository.get_by_id(
        user_id
    )

    if user is None:
        raise authentication_error

    auth_version = payload.get("ver", 0)
    if type(auth_version) is not int or auth_version != user.auth_version:
        raise authentication_error

    return user
