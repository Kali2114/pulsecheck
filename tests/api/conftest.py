from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_now,
    get_password_hasher,
    get_session_factory,
    get_token_service,
)
from app.infrastructure.jwt_token_service import JWTTokenService
from app.main import app
from tests.domain.fakes import FakePasswordHasher

TEST_SECRET_KEY = "test-secret-key-that-is-at-least-32-bytes-long"


@pytest.fixture
def now():
    return datetime(2026, 10, 14, 12, 0, tzinfo=UTC)


@pytest.fixture
def token_service():
    return JWTTokenService(
        secret_key=TEST_SECRET_KEY,
        token_lifetime=timedelta(minutes=30),
    )


@pytest.fixture
def client(session_factory, token_service, now):
    hasher = FakePasswordHasher()

    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_password_hasher] = lambda: hasher
    app.dependency_overrides[get_token_service] = lambda: token_service
    app.dependency_overrides[get_now] = lambda: now

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password",
        },
    )
    assert response.status_code == 201
    data = response.json()

    return {
        "id": data["id"],
        "email": "user@example.com",
        "password": "password",
    }
