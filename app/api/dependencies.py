from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.domain.auth_service import AuthService
from app.domain.exceptions import InvalidToken, UserNotFound
from app.domain.monitor_repository import MonitorRepository
from app.domain.password_hasher import PasswordHasher
from app.domain.user import User
from app.infrastructure.database import SessionLocal
from app.infrastructure.jwt_token_service import JWTTokenService
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from app.infrastructure.password_hasher import BcryptPasswordHasher
from app.infrastructure.user_repository import SQLAlchemyUserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_session_factory() -> sessionmaker[Session]:
    return SessionLocal


def get_db(
    factory: sessionmaker[Session] = Depends(get_session_factory),
) -> Generator[Session, None, None]:
    with factory() as db:
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise


@lru_cache
def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


@lru_cache
def _dummy_hash_for(password_hasher: PasswordHasher) -> str:
    return AuthService.make_dummy_hash(password_hasher)


def get_auth_service(
    db: Session = Depends(get_db),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
) -> AuthService:
    return AuthService(
        user_repository=SQLAlchemyUserRepository(db),
        password_hasher=password_hasher,
        dummy_hash=_dummy_hash_for(password_hasher),
    )


def get_token_service() -> JWTTokenService:
    return JWTTokenService(
        secret_key=settings.secret_key,
        token_lifetime=timedelta(minutes=15),
    )


def get_now() -> datetime:
    return datetime.now(UTC)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    token_service: JWTTokenService = Depends(get_token_service),
    now: datetime = Depends(get_now),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    user_id = token_service.decode_access_token(token, now=now)
    try:
        user = auth_service.get_by_id(user_id)
    except UserNotFound:
        raise InvalidToken("Invalid token") from None
    return user


def get_monitor_repository(
    db: Session = Depends(get_db),
) -> MonitorRepository:
    return SQLAlchemyMonitorRepository(db)
