from datetime import timedelta

import pytest

from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from tests.domain.utils import create_monitor


class TestMonitors:

    def test_post_monitor(self, client, auth_headers, monitor_payload):
        response = client.post("/monitors", json=monitor_payload, headers=auth_headers)
        data = response.json()

        assert response.status_code == 201
        assert isinstance(data.pop("id"), int)
        assert data == {
            "url": "https://example.com",
            "check_interval_seconds": 10,
            "timeout_seconds": 30,
            "retry_count": 3,
            "last_checked_at": None,
        }

    def test_post_monitor_without_token_returns_401(self, client, monitor_payload):
        response = client.post("/monitors", json=monitor_payload)

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("check_interval_seconds", 9),
            ("check_interval_seconds", 86401),
            ("timeout_seconds", 0),
            ("timeout_seconds", 61),
            ("retry_count", 0),
        ],
    )
    def test_invalid_monitor_payload_returns_422(
        self,
        client,
        auth_headers,
        monitor_payload,
        field,
        value,
    ):
        monitor_payload[field] = value
        response = client.post("/monitors", json=monitor_payload, headers=auth_headers)

        assert response.status_code == 422

    def test_get_monitors_returns_only_own_monitors(
        self, client, auth_headers, registered_user, session_factory, make_user
    ):
        monitor1 = create_monitor(
            user_id=registered_user["id"],
            url="https://one.com",
            check_interval=timedelta(seconds=10),
        )

        monitor2 = create_monitor(
            user_id=registered_user["id"],
            url="https://two.com",
            check_interval=timedelta(seconds=10),
        )
        another_user_id = make_user()
        another_monitor = create_monitor(
            user_id=another_user_id,
            url="https://other-user.com",
            check_interval=timedelta(seconds=10),
        )

        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)

            saved_monitor1 = repo.add_monitor(monitor1)
            saved_monitor2 = repo.add_monitor(monitor2)
            repo.add_monitor(another_monitor)

            session.commit()

        response = client.get("/monitors", headers=auth_headers)
        data = response.json()

        assert response.status_code == 200
        returned_ids = [item["id"] for item in data]
        assert returned_ids == [saved_monitor1.id, saved_monitor2.id]

    def test_get_monitors_returns_200_when_empty(self, client, auth_headers):
        response = client.get("/monitors", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_monitors_returns_401_without_authentication(self, client):
        response = client.get("/monitors")

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}
