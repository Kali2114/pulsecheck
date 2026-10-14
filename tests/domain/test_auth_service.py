import re

import pytest

from app.domain.auth_service import MAX_PASSWORD_BYTES, AuthService
from app.domain.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    PasswordTooLong,
)
from app.domain.user_repository import InMemoryUserRepository
from tests.domain.fakes import FakePasswordHasher


class TestAuthService:
    def setup_method(self):
        self.repo = InMemoryUserRepository()
        self.hasher = FakePasswordHasher()
        self.service = AuthService(
            user_repository=self.repo,
            password_hasher=self.hasher,
            dummy_hash=AuthService.make_dummy_hash(self.hasher),
        )

    def test_register_success(self):
        user = self.service.register(
            email=" Kamil@X.com ",
            password="secret123",
        )

        assert user.email == "kamil@x.com"
        assert user.hashed_password == "hashed:secret123"
        assert self.repo.get_by_email("kamil@x.com") == user

    def test_register_accepts_password_of_exactly_max_bytes(self):
        password = "a" * MAX_PASSWORD_BYTES

        user = self.service.register(email="user@example.com", password=password)

        assert self.repo.get_by_email("user@example.com") == user

    def test_register_rejects_password_over_max_bytes(self):
        password = "a" * (MAX_PASSWORD_BYTES + 1)

        with pytest.raises(PasswordTooLong):
            self.service.register(email="user@example.com", password=password)

        assert self.repo.users == []

    def test_register_password_limit_counts_bytes_not_characters(self):
        password = "ą" * 37

        with pytest.raises(PasswordTooLong):
            self.service.register(email="user@example.com", password=password)

        assert self.repo.users == []

    def test_register_rejects_duplicate_email_ignoring_case(self):
        self.service.register(
            email=" Kamil@X.com ",
            password="secret123",
        )
        with pytest.raises(
            EmailAlreadyRegistered,
            match=rf"Email {re.escape('kamil@x.com')} already registered",
        ):
            self.service.register(
                email=" kamil@X.com ",
                password="secret123",
            )

        assert len(self.repo.users) == 1

    def test_login_success_normalized_email(self):
        user = self.service.register(
            email="test@example.com",
            password="test_pass",
        )
        logged_user = self.service.login("Test@example.com ", "test_pass")

        assert logged_user.email == "test@example.com"
        assert logged_user.id == user.id

    def test_login_rejects_unknown_email(self):
        with pytest.raises(InvalidCredentials):
            self.service.login("bademail@example.com", "test_pass")

    def test_login_rejects_wrong_password(self):
        user = self.service.register(
            email="Test@example.com",
            password="test_pass",
        )
        with pytest.raises(InvalidCredentials):
            self.service.login(user.email, "wrong_pass")

    def test_login_verifies_a_password_even_for_unknown_email(self):
        with pytest.raises(InvalidCredentials):
            self.service.login("unknown@example.com", "test_pass")

        assert len(self.hasher.verify_calls) == 1

    def test_login_with_dummy_password_for_unknown_email_is_rejected(self):
        with pytest.raises(InvalidCredentials):
            self.service.login("unknown@example.com", AuthService.DUMMY_PASSWORD)

    def test_make_dummy_hash_hashes_the_dummy_password(self):
        dummy_hash = AuthService.make_dummy_hash(self.hasher)

        assert self.hasher.verify(AuthService.DUMMY_PASSWORD, dummy_hash)

    def test_constructing_the_service_does_not_hash(self):
        hasher = FakePasswordHasher()

        AuthService(
            user_repository=self.repo,
            password_hasher=hasher,
            dummy_hash="hashed:precomputed",
        )

        assert hasher.hash_calls == []

    def test_login_for_unknown_email_verifies_against_the_given_dummy_hash(self):
        with pytest.raises(InvalidCredentials):
            self.service.login("unknown@example.com", "test_pass")

        assert self.hasher.verify_calls == [
            ("test_pass", AuthService.make_dummy_hash(self.hasher))
        ]
