from app.domain.exceptions import EmailAlreadyRegistered, InvalidCredentials
from app.domain.password_hasher import PasswordHasher
from app.domain.user import User
from app.domain.user_repository import UserRepository


def normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    DUMMY_PASSWORD = "not-a-real-password"

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self._dummy_hash = password_hasher.hash(self.DUMMY_PASSWORD)

    def register(self, email: str, password: str) -> User:
        normalized_email = normalize_email(email)
        if self.user_repository.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegistered("Email already registered.")
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
            raise InvalidCredentials("Invalid credentials.")
        return user
