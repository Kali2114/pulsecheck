from datetime import UTC, datetime, timedelta

import pytest

from app.infrastructure.check_result_repository import SQLAlchemyCheckResultRepository
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from tests.domain.utils import create_check_result, create_monitor


class TestCheckResults:
    @pytest.fixture(autouse=True)
    def setup(self, session_factory):
        self.session_factory = session_factory

    def add_monitor(self, user_id, url="https://example.com"):
        with self.session_factory() as session:
            saved = SQLAlchemyMonitorRepository(session).add_monitor(
                create_monitor(
                    user_id=user_id, url=url, check_interval=timedelta(seconds=10)
                )
            )
            session.commit()
        return saved

    def add_check_results(self, *check_results):
        with self.session_factory() as session:
            repository = SQLAlchemyCheckResultRepository(session)
            for check_result in check_results:
                repository.add_check_result(check_result)
            session.commit()

    def test_no_check_results_returns_empty_list(
        self, client, registered_user, auth_headers
    ):
        monitor = self.add_monitor(registered_user["id"])

        response = client.get(
            f"/monitors/{monitor.id}/check-results", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_check_results_oldest_first(
        self, client, registered_user, auth_headers
    ):
        monitor = self.add_monitor(registered_user["id"])
        self.add_check_results(
            create_check_result(
                monitor_id=monitor.id,
                checked_at=datetime(2026, 10, 14, 11, 50, tzinfo=UTC),
                is_up=False,
                response_time_ms=None,
            ),
            create_check_result(
                monitor_id=monitor.id,
                checked_at=datetime(2026, 10, 14, 11, 30, tzinfo=UTC),
                is_up=True,
                response_time_ms=120,
            ),
        )

        response = client.get(
            f"/monitors/{monitor.id}/check-results", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == [
            {
                "checked_at": "2026-10-14T11:30:00Z",
                "is_up": True,
                "response_time_ms": 120,
            },
            {
                "checked_at": "2026-10-14T11:50:00Z",
                "is_up": False,
                "response_time_ms": None,
            },
        ]

    def test_returns_only_given_monitors_check_results(
        self, client, registered_user, auth_headers
    ):
        monitor = self.add_monitor(registered_user["id"], url="https://one.com")
        other_monitor = self.add_monitor(registered_user["id"], url="https://two.com")
        self.add_check_results(
            create_check_result(
                monitor_id=other_monitor.id,
                checked_at=datetime(2026, 10, 14, 11, 40, tzinfo=UTC),
                response_time_ms=999,
            ),
            create_check_result(
                monitor_id=monitor.id,
                checked_at=datetime(2026, 10, 14, 11, 45, tzinfo=UTC),
                response_time_ms=100,
            ),
        )

        response = client.get(
            f"/monitors/{monitor.id}/check-results", headers=auth_headers
        )

        assert response.status_code == 200
        assert [item["response_time_ms"] for item in response.json()] == [100]

    def test_other_users_monitor_returns_404(
        self, client, registered_user, auth_headers, make_user
    ):
        other_monitor = self.add_monitor(make_user())
        self.add_check_results(
            create_check_result(
                monitor_id=other_monitor.id,
                checked_at=datetime(2026, 10, 14, 11, 45, tzinfo=UTC),
            )
        )

        response = client.get(
            f"/monitors/{other_monitor.id}/check-results", headers=auth_headers
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": f"Monitor with id {other_monitor.id} not found"
        }

    def test_unknown_monitor_returns_404(self, client, registered_user, auth_headers):
        monitor = self.add_monitor(registered_user["id"])
        unknown_id = monitor.id + 1

        response = client.get(
            f"/monitors/{unknown_id}/check-results", headers=auth_headers
        )

        assert response.status_code == 404
        assert response.json() == {"detail": f"Monitor with id {unknown_id} not found"}

    def test_without_token_returns_401(self, client):
        response = client.get("/monitors/1/check-results")

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}
