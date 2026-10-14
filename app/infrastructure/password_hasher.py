import bcrypt

from app.domain.auth_service import MAX_PASSWORD_BYTES
from app.domain.exceptions import PasswordTooLong


class BcryptPasswordHasher:

    def __init__(self, rounds: int = 12) -> None:
        self.rounds = rounds

    def hash(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > MAX_PASSWORD_BYTES:
            raise PasswordTooLong("Password too long")
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify(self, password: str, hashed_password: str) -> bool:
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > MAX_PASSWORD_BYTES:
            return False
        hashed_password_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)
