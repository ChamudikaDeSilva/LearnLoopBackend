from datetime import (
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hasher = PasswordHash.recommended()


def hash_password(
    password: str,
) -> str:
    return password_hasher.hash(
        password
    )


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    user_id: int,
    auth_version: int = 0,
) -> str:

    if not settings.jwt_secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured."
        )

    now = datetime.now(
        timezone.utc
    )

    expires_at = now + timedelta(
        minutes=(
            settings
            .jwt_access_token_expire_minutes
        )
    )

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expires_at,
        "ver": auth_version,
        "jti": uuid4().hex,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(
    token: str,
) -> dict:

    if not settings.jwt_secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured."
        )

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[
            settings.jwt_algorithm
        ],
    )
