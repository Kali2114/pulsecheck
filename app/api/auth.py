from datetime import datetime

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_auth_service, get_now, get_token_service
from app.api.schemas import TokenResponse, UserCreate, UserRead
from app.domain.auth_service import AuthService
from app.domain.user import User
from app.infrastructure.jwt_token_service import JWTTokenService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreate, auth_service: AuthService = Depends(get_auth_service)
) -> User:
    new_user = auth_service.register(email=payload.email, password=payload.password)
    return new_user


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    token_service: JWTTokenService = Depends(get_token_service),
    now: datetime = Depends(get_now),
) -> TokenResponse:
    user = auth_service.login(form_data.username, form_data.password)
    token = token_service.create_access_token(user.id, now)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )
