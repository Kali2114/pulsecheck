from collections.abc import Generator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from app.domain.auth_service import AuthService
from app.domain.password_hasher import PasswordHasher
from app.infrastructure.database import SessionLocal
from app.infrastructure.password_hasher import BcryptPasswordHasher
from app.infrastructure.user_repository import SQLAlchemyUserRepository


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
