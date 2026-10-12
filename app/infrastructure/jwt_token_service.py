from datetime import UTC, datetime, timedelta

import jwt
from jwt import PyJWTError

from app.domain.exceptions import InvalidToken


class JWTTokenService:
    def __init__(self, secret_key: str, token_lifetime: timedelta) -> None:
        self.secret_key = secret_key
        self.token_lifetime = token_lifetime

    def create_access_token(self, user_id: int, now: datetime) -> str:
        expires_at = now + self.token_lifetime
        payload = {
            "sub": str(user_id),
            "exp": expires_at,
        }
        token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        return token

    def decode_access_token(self, token: str, now: datetime) -> int:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=["HS256"],
                options={"verify_exp": False, "require": ["sub", "exp"]},
            )
        except PyJWTError:
            raise InvalidToken("Invalid token") from None
        expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
        if now >= expires_at:
            raise InvalidToken("Token expired")
        return int(payload["sub"])
