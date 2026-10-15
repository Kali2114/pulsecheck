from app.domain.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    PasswordTooLong,
)
from app.domain.password_hasher import PasswordHasher
from app.domain.user import User
from app.domain.user_repository import UserRepository

MAX_PASSWORD_BYTES = 72


def normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    DUMMY_PASSWORD = "not-a-real-password"

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        dummy_hash: str,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self._dummy_hash = dummy_hash

    @classmethod
    def make_dummy_hash(cls, password_hasher: PasswordHasher) -> str:
        return password_hasher.hash(cls.DUMMY_PASSWORD)

    def register(self, email: str, password: str) -> User:
        normalized_email = normalize_email(email)
        if self.user_repository.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegistered(normalized_email)
        check_password = password.encode("utf-8")
        if len(check_password) > MAX_PASSWORD_BYTES:
            raise PasswordTooLong("Password is too long")
        hashed_password = self.password_hasher.hash(password)
        user = User(email=normalized_email, hashed_password=hashed_password)
        added_user = self.user_repository.add_user(user)
        return added_user

    def login(self, email: str, password: str) -> User:
        normalized_email = normalize_email(email)
        user = self.user_repository.get_by_email(normalized_email)
        hashed_password = user.hashed_password if user else self._dummy_hash
        password_matches = self.password_hasher.verify(password, hashed_password)
        if user is None or not password_matches:
            raise InvalidCredentials("Invalid credentials")
        return user

    def get_by_id(self, user_id: int) -> User:
        return self.user_repository.get_by_id(user_id)
