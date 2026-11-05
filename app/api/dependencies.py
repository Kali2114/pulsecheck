from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import AwareDatetime
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.domain.auth_service import AuthService
from app.domain.check_result_repository import CheckResultRepository
from app.domain.exceptions import InvalidToken, MonitorNotFound, UserNotFound
from app.domain.monitor import Monitor
from app.domain.monitor_repository import MonitorRepository
from app.domain.password_hasher import PasswordHasher
from app.domain.user import User
from app.infrastructure.check_result_repository import SQLAlchemyCheckResultRepository
from app.infrastructure.database import SessionLocal
from app.infrastructure.jwt_token_service import JWTTokenService
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from app.infrastructure.password_hasher import BcryptPasswordHasher
from app.infrastructure.user_repository import SQLAlchemyUserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

CHECK_RESULTS_DEFAULT_WINDOW = timedelta(hours=1)
CHECK_RESULTS_MAX_AGE = timedelta(days=7)


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


def get_check_results_since(
    since: AwareDatetime | None = Query(default=None),
    now: datetime = Depends(get_now),
) -> datetime:
    if since is None:
        return now - CHECK_RESULTS_DEFAULT_WINDOW
    if since < now - CHECK_RESULTS_MAX_AGE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"since must be at most {CHECK_RESULTS_MAX_AGE.days} days ago",
        )
    return since


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


def get_check_result_repository(
    db: Session = Depends(get_db),
) -> CheckResultRepository:
    return SQLAlchemyCheckResultRepository(db)


def get_current_user_monitor(
    monitor_id: int,
    current_user: User = Depends(get_current_user),
    monitor_repository: MonitorRepository = Depends(get_monitor_repository),
) -> Monitor:
    received_monitor = monitor_repository.get_monitor(monitor_id)
    if received_monitor.user_id != current_user.id:
        raise MonitorNotFound(monitor_id)
    return received_monitor
