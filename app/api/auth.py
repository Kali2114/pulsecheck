from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_auth_service
from app.api.schemas import UserCreate, UserRead
from app.domain.auth_service import AuthService
from app.domain.user import User

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
