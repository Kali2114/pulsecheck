import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_password_hasher, get_session_factory
from app.main import app
from tests.domain.fakes import FakePasswordHasher


@pytest.fixture
def client(session_factory):
    hasher = FakePasswordHasher()

    app.dependency_overrides[get_session_factory] = lambda: session_factory
    app.dependency_overrides[get_password_hasher] = lambda: hasher

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
