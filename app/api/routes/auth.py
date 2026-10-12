from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
)
from app.core.database import get_db
from app.core.profile_rate_limit import (
    ProfileReauthenticationLimiter,
    ReauthenticationRateLimitError,
)
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
)
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    IncorrectCurrentPasswordError,
    StaleAuthenticationError,
    UnchangedPasswordError,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

reauthentication_limiter = ProfileReauthenticationLimiter()


def check_reauthentication_limit(user_id: int, request: Request) -> None:
    address = request.client.host if request.client is not None else "unknown"
    try:
        reauthentication_limiter.check(user_id, address)
    except ReauthenticationRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password attempts. Try again in a few minutes.",
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


def account_error_response(exc: Exception) -> HTTPException:
    if isinstance(exc, EmailAlreadyRegisteredError):
        return HTTPException(status_code=409, detail="An account with this email already exists.")
    if isinstance(exc, IncorrectCurrentPasswordError):
        return HTTPException(status_code=400, detail="Your current password is incorrect.")
    if isinstance(exc, UnchangedPasswordError):
        return HTTPException(status_code=400, detail="Choose a password different from your current password.")
    return HTTPException(
        status_code=401,
        detail="Your account credentials changed. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(
        db
    )

    try:
        return auth_service.register(
            request
        )

    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "An account with this "
                "email already exists."
            ),
        )


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    auth_service = AuthService(
        db
    )

    try:
        user, access_token = (
            auth_service.login(
                request
            )
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user,
        }

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password."
            ),
            headers={
                "WWW-Authenticate": (
                    "Bearer"
                )
            },
        )


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(
        get_current_user
    ),
):
    return current_user


@router.patch("/me", response_model=LoginResponse)
def update_me(
    payload: UpdateProfileRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expected_auth_version = current_user.auth_version
    if str(payload.email).strip().lower() != current_user.email.strip().lower():
        check_reauthentication_limit(current_user.id, request)
    try:
        user, token = AuthService(db).update_profile(
            current_user.id, expected_auth_version, payload
        )
        return {"user": user, "access_token": token, "token_type": "bearer"}
    except (
        EmailAlreadyRegisteredError,
        IncorrectCurrentPasswordError,
        StaleAuthenticationError,
    ) as exc:
        raise account_error_response(exc) from exc


@router.post("/change-password", response_model=LoginResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expected_auth_version = current_user.auth_version
    check_reauthentication_limit(current_user.id, request)
    try:
        user, token = AuthService(db).change_password(
            current_user.id, expected_auth_version, payload
        )
        return {"user": user, "access_token": token, "token_type": "bearer"}
    except (
        IncorrectCurrentPasswordError,
        UnchangedPasswordError,
        StaleAuthenticationError,
    ) as exc:
        raise account_error_response(exc) from exc
