from app.domain.password_hasher import PasswordHasher
from tests.domain.fakes import FakePasswordHasher


def test_fake_password_hasher_satisfies_password_hasher_protocol():
    assert isinstance(FakePasswordHasher(), PasswordHasher)
