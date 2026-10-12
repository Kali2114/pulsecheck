from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.domain.exceptions import InvalidToken
from app.infrastructure.jwt_token_service import JWTTokenService


class TestJWTTokenService:
    def setup_method(self):
        self.token_life = timedelta(minutes=15)
        self.service = JWTTokenService(
            secret_key="test-secrettest-secrettest-secrettest-secrettest-secrettest-secrettest-secret",
            token_lifetime=self.token_life,
        )
        self.now = datetime(2026, 10, 11, 12, 00, tzinfo=UTC)
        self.expires_at = self.now + self.token_life

    def test_create_and_decode_access_token_returns_user_id(self):
        token = self.service.create_access_token(42, now=self.now)
        user_id = self.service.decode_access_token(token, now=self.now)

        assert user_id == 42

    def test_decode_accepts_token_one_second_before_expiry(self):
        token = self.service.create_access_token(42, now=self.now)
        valid_time = self.expires_at - timedelta(seconds=1)

        user_id = self.service.decode_access_token(token, now=valid_time)

        assert user_id == 42

    def test_decode_rejects_token_at_expiry(self):
        token = self.service.create_access_token(42, now=self.now)
        with pytest.raises(InvalidToken):
            self.service.decode_access_token(token, now=self.expires_at)

    def test_decode_rejects_token_with_wrong_secret(self):
        token = self.service.create_access_token(42, now=self.now)
        next_service = JWTTokenService(
            secret_key="test-secrettest-secrettest-secrettest-secrettest-secrettest-secrettest-secret1",
            token_lifetime=self.token_life,
        )
        with pytest.raises(InvalidToken):
            next_service.decode_access_token(token, now=self.now)

    def test_decode_rejects_tampered_token(self):
        token = self.service.create_access_token(42, now=self.now)
        header, payload, signature = token.split(".")
        index = len(signature) // 2
        new_signature = signature[:index] + "x" + signature[index:]
        tampered_token = ".".join([header, payload, new_signature])
        with pytest.raises(InvalidToken):
            self.service.decode_access_token(tampered_token, now=self.now)

    def test_decode_rejects_garbage_token(self):
        token = "garbage-token"
        with pytest.raises(InvalidToken):
            self.service.decode_access_token(token, now=self.now)

    @pytest.mark.parametrize("missing_claim", ["sub", "exp"])
    def test_decode_rejects_token_missing_required_claim(self, missing_claim):
        payload = {"sub": "42", "exp": self.expires_at}
        del payload[missing_claim]
        token = jwt.encode(payload, self.service.secret_key, algorithm="HS256")

        with pytest.raises(InvalidToken):
            self.service.decode_access_token(token, now=self.now)
