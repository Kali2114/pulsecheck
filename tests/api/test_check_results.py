from datetime import UTC, datetime, timedelta

from tests.domain.utils import create_check_result


class TestCheckResults:

    def test_no_check_results_returns_empty_list(
        self, client, registered_user, auth_headers, add_monitor
    ):
        monitor = add_monitor(registered_user["id"])

        response = client.get(
            f"/monitors/{monitor.id}/check-results", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_check_results_oldest_first(
        self, client, registered_user, auth_headers, add_check_results, add_monitor
    ):
        monitor = add_monitor(registered_user["id"])
        add_check_results(
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
        self, client, registered_user, auth_headers, add_monitor, add_check_results
    ):
        monitor = add_monitor(registered_user["id"], url="https://one.com")
        other_monitor = add_monitor(registered_user["id"], url="https://two.com")
        add_check_results(
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
        self,
        client,
        registered_user,
        auth_headers,
        make_user,
        add_check_results,
        add_monitor,
    ):
        other_monitor = add_monitor(make_user())
        add_check_results(
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

    def test_unknown_monitor_returns_404(
        self, client, registered_user, auth_headers, add_monitor
    ):
        monitor = add_monitor(registered_user["id"])
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

    def test_get_check_results_returns_only_results_since_given_time(
        self, client, registered_user, auth_headers, now, add_monitor, add_check_results
    ):
        monitor = add_monitor(registered_user["id"])
        add_check_results(
            create_check_result(
                monitor_id=monitor.id,
                checked_at=now - timedelta(hours=3),
            ),
            create_check_result(
                monitor_id=monitor.id,
                checked_at=now - timedelta(hours=1, minutes=30),
            ),
        )
        since = now - timedelta(hours=2)
        response = client.get(
            f"/monitors/{monitor.id}/check-results",
            headers=auth_headers,
            params={"since": since.isoformat()},
        )
        data = response.json()

        assert response.status_code == 200
        assert len(data) == 1
        assert data[0]["checked_at"] == "2026-10-14T10:30:00Z"

    def test_without_since_returns_only_last_hour(
        self, client, registered_user, auth_headers, now, add_monitor, add_check_results
    ):
        monitor = add_monitor(registered_user["id"])
        add_check_results(
            create_check_result(
                monitor_id=monitor.id,
                checked_at=now - timedelta(hours=1, seconds=1),
            ),
            create_check_result(
                monitor_id=monitor.id,
                checked_at=now - timedelta(hours=1),
            ),
        )

        response = client.get(
            f"/monitors/{monitor.id}/check-results", headers=auth_headers
        )

        assert response.status_code == 200
        assert [item["checked_at"] for item in response.json()] == [
            "2026-10-14T11:00:00Z"
        ]

    def test_since_exactly_seven_days_ago_is_accepted(
        self, client, registered_user, auth_headers, now, add_monitor, add_check_results
    ):
        monitor = add_monitor(registered_user["id"])
        add_check_results(
            create_check_result(
                monitor_id=monitor.id,
                checked_at=now - timedelta(days=7),
            )
        )
        since = now - timedelta(days=7)

        response = client.get(
            f"/monitors/{monitor.id}/check-results",
            headers=auth_headers,
            params={"since": since.isoformat()},
        )

        assert response.status_code == 200
        assert [item["checked_at"] for item in response.json()] == [
            "2026-10-07T12:00:00Z"
        ]

    def test_since_older_than_seven_days_returns_422(
        self, client, registered_user, auth_headers, now, add_monitor
    ):
        monitor = add_monitor(registered_user["id"])
        since = now - timedelta(days=7, seconds=1)

        response = client.get(
            f"/monitors/{monitor.id}/check-results",
            headers=auth_headers,
            params={"since": since.isoformat()},
        )

        assert response.status_code == 422
        assert response.json() == {"detail": "since must be at most 7 days ago"}

    def test_naive_since_returns_422(
        self, client, registered_user, auth_headers, add_monitor
    ):
        monitor = add_monitor(registered_user["id"])

        response = client.get(
            f"/monitors/{monitor.id}/check-results",
            headers=auth_headers,
            params={"since": "2026-10-14T10:00:00"},
        )

        assert response.status_code == 422
        assert [error["loc"] for error in response.json()["detail"]] == [
            ["query", "since"]
        ]

    def test_future_since_returns_empty_list(
        self, client, registered_user, auth_headers, now, add_monitor, add_check_results
    ):
        monitor = add_monitor(registered_user["id"])
        add_check_results(
            create_check_result(
                monitor_id=monitor.id,
                checked_at=now - timedelta(minutes=10),
            )
        )
        since = now + timedelta(hours=1)

        response = client.get(
            f"/monitors/{monitor.id}/check-results",
            headers=auth_headers,
            params={"since": since.isoformat()},
        )

        assert response.status_code == 200
        assert response.json() == []
