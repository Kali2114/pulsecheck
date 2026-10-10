import pytest

from app.domain.exceptions import PasswordTooLong
from app.domain.password_hasher import PasswordHasher
from app.infrastructure.password_hasher import BcryptPasswordHasher

TEST_ROUNDS = 4


class TestBcryptPasswordHasher:
    def setup_method(self):
        self.hasher = BcryptPasswordHasher(rounds=TEST_ROUNDS)
        self.password = "test_password"

    def test_verify_returns_true_for_correct_password(self):
        hashed_password = self.hasher.hash(self.password)

        assert self.hasher.verify(self.password, hashed_password) is True

    def test_verify_returns_false_for_wrong_password(self):
        hashed_password = self.hasher.hash(self.password)

        assert self.hasher.verify("wrong_password", hashed_password) is False

    def test_hashing_same_password_twice_returns_different_hashes(self):
        hashed_password = self.hasher.hash(self.password)
        second_hashed_password = self.hasher.hash(self.password)

        assert hashed_password != self.password
        assert hashed_password != second_hashed_password
        assert self.hasher.verify(self.password, hashed_password) is True
        assert self.hasher.verify(self.password, second_hashed_password) is True

    def test_hashing_raises_when_password_exceeds_72_bytes(self):
        password = "a" * (BcryptPasswordHasher.MAX_PASSWORD_BYTES + 1)

        with pytest.raises(PasswordTooLong):
            self.hasher.hash(password)

    def test_verify_returns_false_for_password_over_72_bytes(self):
        hashed_password = self.hasher.hash(self.password)
        too_long = "a" * (BcryptPasswordHasher.MAX_PASSWORD_BYTES + 1)

        assert self.hasher.verify(too_long, hashed_password) is False

    def test_hashing_accepts_password_of_exactly_72_bytes(self):
        password = "a" * BcryptPasswordHasher.MAX_PASSWORD_BYTES

        hashed_password = self.hasher.hash(password)

        assert self.hasher.verify(password, hashed_password) is True

    def test_hashing_limit_counts_bytes_not_characters(self):
        password = "ą" * 37

        with pytest.raises(PasswordTooLong):
            self.hasher.hash(password)

    def test_default_cost_is_12_rounds(self):
        hashed_password = BcryptPasswordHasher().hash(self.password)

        assert hashed_password.startswith("$2b$12$")

    def test_bcrypt_password_hasher_satisfies_password_hasher_protocol(self):
        assert isinstance(self.hasher, PasswordHasher)
