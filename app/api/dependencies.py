from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database import SessionLocal


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
