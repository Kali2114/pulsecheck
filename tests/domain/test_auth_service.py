import pytest

from app.domain.auth_service import AuthService
from app.domain.exceptions import EmailAlreadyRegistered
from app.domain.user_repository import InMemoryUserRepository
from tests.domain.fakes import FakePasswordHasher


class TestAuthService:
    def setup_method(self):
        self.repo = InMemoryUserRepository()
        self.hasher = FakePasswordHasher()
        self.service = AuthService(
            user_repository=self.repo,
            password_hasher=self.hasher,
        )

    def test_register_success(self):
        user = self.service.register(
            email=" Kamil@X.com ",
            password="secret123",
        )

        assert user.email == "kamil@x.com"
        assert user.hashed_password == "hashed:secret123"
        assert self.repo.get_by_email("kamil@x.com") == user

    def test_register_rejects_duplicate_email_ignoring_case(self):
        self.service.register(
            email=" Kamil@X.com ",
            password="secret123",
        )
        with pytest.raises(EmailAlreadyRegistered):
            self.service.register(
                email=" kamil@X.com ",
                password="secret123",
            )

        assert len(self.repo.users) == 1
