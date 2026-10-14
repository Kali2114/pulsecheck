from datetime import UTC, datetime

import pytest

from app.api.dependencies import (
    get_auth_service,
    get_db,
    get_now,
    get_password_hasher,
    get_session_factory,
    get_token_service,
)
from app.config import settings
from app.domain.auth_service import AuthService
from app.infrastructure.database import SessionLocal
from app.infrastructure.jwt_token_service import JWTTokenService
from app.infrastructure.password_hasher import BcryptPasswordHasher
from app.infrastructure.user_repository import SQLAlchemyUserRepository
from tests.domain.fakes import FakePasswordHasher
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


class TestAuthDependencies:
    def test_password_hasher_is_one_shared_bcrypt_hasher(self):
        hasher = get_password_hasher()

        assert isinstance(hasher, BcryptPasswordHasher)
        assert get_password_hasher() is hasher

    def test_auth_service_uses_the_request_session(self, db_session):
        auth_service = get_auth_service(db_session, FakePasswordHasher())

        user = auth_service.register(email="new@example.com", password="secret123")

        saved = SQLAlchemyUserRepository(db_session).get_by_email("new@example.com")
        assert isinstance(auth_service, AuthService)
        assert saved is not None
        assert saved.id == user.id

    def test_auth_service_hashes_the_dummy_password_only_once(self, db_session):
        hasher = FakePasswordHasher()

        get_auth_service(db_session, hasher)
        get_auth_service(db_session, hasher)

        assert hasher.hash_calls == [AuthService.DUMMY_PASSWORD]


class TestTokenAndClockDependencies:
    def test_token_service_signs_with_the_configured_secret_key(self):
        now = datetime(2026, 10, 14, 12, 0, tzinfo=UTC)
        token = get_token_service().create_access_token(42, now=now)

        verifier = JWTTokenService(
            secret_key=settings.secret_key,
            token_lifetime=get_token_service().token_lifetime,
        )

        assert verifier.decode_access_token(token, now=now) == 42

    def test_now_returns_the_current_utc_time(self):
        before = datetime.now(UTC)
        result = get_now()
        after = datetime.now(UTC)

        assert result.tzinfo == UTC
        assert before <= result <= after
