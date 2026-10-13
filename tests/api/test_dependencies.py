import pytest

from app.api.dependencies import get_db, get_session_factory
from app.infrastructure.database import SessionLocal
from app.infrastructure.user_repository import SQLAlchemyUserRepository
from tests.domain.utils import create_user


class TestGetDb:
    def test_commits_when_the_request_succeeds(self, session_factory):
        db_generator = get_db(session_factory)
        session = next(db_generator)
        SQLAlchemyUserRepository(session).add_user(create_user())

        with pytest.raises(StopIteration):
            next(db_generator)

        with session_factory() as new_session:
            saved = SQLAlchemyUserRepository(new_session).get_by_email(
                create_user().email
            )
        assert saved is not None

    def test_rolls_back_and_reraises_when_the_request_fails(self, session_factory):
        db_generator = get_db(session_factory)
        session = next(db_generator)
        SQLAlchemyUserRepository(session).add_user(create_user())

        with pytest.raises(RuntimeError, match="boom"):
            db_generator.throw(RuntimeError("boom"))

        with session_factory() as new_session:
            saved = SQLAlchemyUserRepository(new_session).get_by_email(
                create_user().email
            )
        assert saved is None

    def test_get_session_factory_returns_session_local(self):
        factory = get_session_factory()

        assert factory is SessionLocal
