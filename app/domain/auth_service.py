from app.domain.exceptions import EmailAlreadyRegistered
from app.domain.password_hasher import PasswordHasher
from app.domain.user import User
from app.domain.user_repository import UserRepository


def normalize_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher

    def register(self, email: str, password: str) -> User:
        normalized_email = normalize_email(email)
        if self.user_repository.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegistered("Email already registered.")
        hashed_password = self.password_hasher.hash(password)
        user = User(email=normalized_email, hashed_password=hashed_password)
        added_user = self.user_repository.add_user(user)
        return added_user
