from datetime import timedelta

import pytest

from app.domain.exceptions import MonitorNotFound
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

    def test_get_monitor_returns_own_monitor(
        self, client, auth_headers, session_factory, registered_user
    ):
        monitor1 = create_monitor(
            user_id=registered_user["id"],
            url="https://first.example.com",
            check_interval=timedelta(seconds=10),
            retry_count=5,
            timeout=20,
        )

        monitor2 = create_monitor(
            user_id=registered_user["id"],
            url="https://second.example.com",
            check_interval=timedelta(seconds=15),
            retry_count=7,
            timeout=30,
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor1 = repo.add_monitor(monitor1)
            saved_monitor2 = repo.add_monitor(monitor2)
            session.commit()

        response1 = client.get(f"/monitors/{saved_monitor1.id}", headers=auth_headers)
        response2 = client.get(f"/monitors/{saved_monitor2.id}", headers=auth_headers)
        data1 = response1.json()
        data2 = response2.json()

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert data1["id"] == saved_monitor1.id
        assert data1["url"] == "https://first.example.com"
        assert data1["last_checked_at"] is None
        assert data1["retry_count"] == 5
        assert data1["check_interval_seconds"] == 10
        assert data1["timeout_seconds"] == 20
        assert data2["id"] == saved_monitor2.id
        assert data2["url"] == "https://second.example.com"
        assert data2["last_checked_at"] is None
        assert data2["retry_count"] == 7
        assert data2["check_interval_seconds"] == 15
        assert data2["timeout_seconds"] == 30

    def test_get_monitor_unknown_id_returns_404(
        self, client, auth_headers, session_factory, registered_user
    ):
        monitor = create_monitor(
            user_id=registered_user["id"],
            check_interval=timedelta(seconds=10),
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(monitor)
            session.commit()
        unknown_id = saved_monitor.id + 1
        response = client.get(f"/monitors/{unknown_id}", headers=auth_headers)

        assert response.status_code == 404
        assert response.json() == {"detail": f"Monitor with id {unknown_id} not found"}

    def test_get_monitor_another_user_returns_404(
        self, client, auth_headers, session_factory, make_user
    ):
        another_user_id = make_user()
        another_monitor = create_monitor(
            user_id=another_user_id,
            check_interval=timedelta(seconds=10),
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(another_monitor)
            session.commit()

        response = client.get(f"/monitors/{saved_monitor.id}", headers=auth_headers)

        assert response.status_code == 404
        assert response.json() == {
            "detail": f"Monitor with id {saved_monitor.id} not found"
        }

    def test_get_monitor_returns_401_without_authentication(self, client):
        response = client.get("/monitors/4")

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

    def test_patch_monitor_changes_all_sent_fields(
        self, client, auth_headers, session_factory, registered_user
    ):
        monitor = create_monitor(
            user_id=registered_user["id"],
            url="https://original.example.com",
            check_interval=timedelta(seconds=10),
            timeout=20,
            retry_count=3,
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(monitor)
            session.commit()

        payload = {
            "url": "https://change.example.com",
            "check_interval_seconds": 99,
            "timeout_seconds": 40,
            "retry_count": 5,
        }
        response = client.patch(
            f"/monitors/{saved_monitor.id}", json=payload, headers=auth_headers
        )
        expected = {
            "id": saved_monitor.id,
            "url": "https://change.example.com",
            "check_interval_seconds": 99,
            "timeout_seconds": 40,
            "retry_count": 5,
            "last_checked_at": None,
        }

        assert response.status_code == 200
        assert response.json() == expected

        reread = client.get(f"/monitors/{saved_monitor.id}", headers=auth_headers)
        assert reread.json() == expected

    def test_patch_monitor_changes_only_sent_fields(
        self, client, auth_headers, session_factory, registered_user
    ):
        monitor = create_monitor(
            user_id=registered_user["id"],
            url="https://original.example.com",
            check_interval=timedelta(seconds=15),
            timeout=20,
            retry_count=3,
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(monitor)
            session.commit()

        response = client.patch(
            f"/monitors/{saved_monitor.id}",
            json={"url": "https://change.example.com"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json() == {
            "id": saved_monitor.id,
            "url": "https://change.example.com",
            "check_interval_seconds": 15,
            "timeout_seconds": 20,
            "retry_count": 3,
            "last_checked_at": None,
        }

    def test_patch_monitor_rejects_unknown_field(
        self, client, auth_headers, session_factory, registered_user, make_user
    ):
        monitor = create_monitor(
            user_id=registered_user["id"],
            url="https://original.example.com",
            check_interval=timedelta(seconds=10),
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(monitor)
            session.commit()

        response = client.patch(
            f"/monitors/{saved_monitor.id}",
            json={"user_id": make_user()},
            headers=auth_headers,
        )

        assert response.status_code == 422
        reread = client.get(f"/monitors/{saved_monitor.id}", headers=auth_headers)
        assert reread.status_code == 200

    @pytest.mark.parametrize(
        "field",
        ["url", "check_interval_seconds", "timeout_seconds", "retry_count"],
    )
    def test_patch_monitor_rejects_null(
        self, client, auth_headers, session_factory, registered_user, field
    ):
        monitor = create_monitor(
            user_id=registered_user["id"],
            url="https://original.example.com",
            check_interval=timedelta(seconds=10),
            timeout=20,
            retry_count=3,
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(monitor)
            session.commit()

        response = client.patch(
            f"/monitors/{saved_monitor.id}",
            json={field: None},
            headers=auth_headers,
        )

        assert response.status_code == 422
        reread = client.get(f"/monitors/{saved_monitor.id}", headers=auth_headers)
        assert reread.json() == {
            "id": saved_monitor.id,
            "url": "https://original.example.com",
            "check_interval_seconds": 10,
            "timeout_seconds": 20,
            "retry_count": 3,
            "last_checked_at": None,
        }

    def test_patch_monitor_rejects_invalid_value(
        self, client, auth_headers, session_factory, registered_user
    ):
        monitor = create_monitor(
            user_id=registered_user["id"],
            check_interval=timedelta(seconds=10),
            timeout=20,
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(monitor)
            session.commit()

        response = client.patch(
            f"/monitors/{saved_monitor.id}",
            json={"timeout_seconds": 0},
            headers=auth_headers,
        )

        assert response.status_code == 422
        reread = client.get(f"/monitors/{saved_monitor.id}", headers=auth_headers)
        assert reread.json()["timeout_seconds"] == 20

    def test_patch_monitor_another_user_returns_404(
        self, client, auth_headers, session_factory, make_user
    ):
        another_monitor = create_monitor(
            user_id=make_user(),
            url="https://other-user.example.com",
            check_interval=timedelta(seconds=10),
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(another_monitor)
            session.commit()

        response = client.patch(
            f"/monitors/{saved_monitor.id}",
            json={"url": "https://hijacked.example.com"},
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": f"Monitor with id {saved_monitor.id} not found"
        }
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            assert (
                repo.get_monitor(saved_monitor.id).url
                == "https://other-user.example.com"
            )

    def test_patch_monitor_returns_401_without_authentication(self, client):
        response = client.patch("/monitors/4", json={"url": "https://x.example.com"})

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

    def test_delete_monitor(
        self, client, auth_headers, registered_user, session_factory
    ):
        monitor = create_monitor(
            user_id=registered_user["id"],
            url="https://original.example.com",
            check_interval=timedelta(seconds=10),
        )

        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(monitor)
            session.commit()

        response = client.delete(f"/monitors/{saved_monitor.id}", headers=auth_headers)

        assert response.status_code == 204
        assert response.content == b""
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            with pytest.raises(MonitorNotFound):
                repo.get_monitor(saved_monitor.id)

    def test_delete_monitor_another_user_returns_404(
        self, client, auth_headers, session_factory, make_user
    ):
        another_monitor = create_monitor(
            user_id=make_user(),
            check_interval=timedelta(seconds=10),
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(another_monitor)
            session.commit()

        response = client.delete(f"/monitors/{saved_monitor.id}", headers=auth_headers)

        assert response.status_code == 404
        assert response.json() == {
            "detail": f"Monitor with id {saved_monitor.id} not found"
        }

        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            repo.get_monitor(saved_monitor.id)

    def test_delete_monitor_returns_401_without_authentication(
        self, client, session_factory, registered_user
    ):
        monitor = create_monitor(
            user_id=registered_user["id"],
            check_interval=timedelta(seconds=10),
        )
        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            saved_monitor = repo.add_monitor(monitor)
            session.commit()

        response = client.delete(f"/monitors/{saved_monitor.id}")

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

        with session_factory() as session:
            repo = SQLAlchemyMonitorRepository(session)
            repo.get_monitor(saved_monitor.id)
