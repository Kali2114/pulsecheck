from datetime import timedelta

from tests.domain.utils import create_check_result


class TestMonitorStats:

    def test_returns_uptime_and_average_response_time(
        self, registered_user, auth_headers, client, add_monitor, add_check_results, now
    ):
        monitor = add_monitor(registered_user["id"])
        add_check_results(
            create_check_result(
                monitor_id=monitor.id, checked_at=now, response_time_ms=70
            ),
            create_check_result(
                monitor_id=monitor.id, checked_at=now, response_time_ms=100
            ),
            create_check_result(
                monitor_id=monitor.id, checked_at=now, response_time_ms=130
            ),
            create_check_result(
                monitor_id=monitor.id, checked_at=now, is_up=False, response_time_ms=50
            ),
        )

        response = client.get(f"/monitors/{monitor.id}/stats", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            "uptime_percentage": 75.0,
            "average_response_time_ms": 100,
            "check_count": 4,
        }

    def test_stats_uses_default_time_window(
        self, registered_user, auth_headers, client, add_monitor, add_check_results, now
    ):
        monitor = add_monitor(registered_user["id"])
        add_check_results(
            create_check_result(
                monitor_id=monitor.id, checked_at=now - timedelta(hours=1, seconds=1)
            ),
            create_check_result(
                monitor_id=monitor.id, checked_at=now - timedelta(minutes=30)
            ),
        )
        response = client.get(f"/monitors/{monitor.id}/stats", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["check_count"] == 1

    def test_no_checks_returns_nulls_and_zero_count(
        self, registered_user, auth_headers, client, add_monitor
    ):
        monitor = add_monitor(registered_user["id"])

        response = client.get(f"/monitors/{monitor.id}/stats", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            "uptime_percentage": None,
            "average_response_time_ms": None,
            "check_count": 0,
        }

    def test_all_checks_down_without_response_returns_zero_uptime(
        self, registered_user, auth_headers, client, add_monitor, add_check_results, now
    ):
        monitor = add_monitor(registered_user["id"])
        add_check_results(
            create_check_result(
                monitor_id=monitor.id,
                checked_at=now - timedelta(minutes=20),
                is_up=False,
                response_time_ms=None,
            ),
            create_check_result(
                monitor_id=monitor.id,
                checked_at=now - timedelta(minutes=10),
                is_up=False,
                response_time_ms=None,
            ),
        )

        response = client.get(f"/monitors/{monitor.id}/stats", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == {
            "uptime_percentage": 0.0,
            "average_response_time_ms": None,
            "check_count": 2,
        }

    def test_other_users_monitor_returns_404(
        self, auth_headers, client, add_monitor, add_check_results, make_user, now
    ):
        other_monitor = add_monitor(make_user())
        add_check_results(
            create_check_result(
                monitor_id=other_monitor.id,
                checked_at=now - timedelta(minutes=10),
            )
        )

        response = client.get(
            f"/monitors/{other_monitor.id}/stats", headers=auth_headers
        )

        assert response.status_code == 404
        assert response.json() == {
            "detail": f"Monitor with id {other_monitor.id} not found"
        }

    def test_unknown_monitor_returns_404(
        self, registered_user, auth_headers, client, add_monitor
    ):
        monitor = add_monitor(registered_user["id"])
        unknown_id = monitor.id + 1

        response = client.get(f"/monitors/{unknown_id}/stats", headers=auth_headers)

        assert response.status_code == 404
        assert response.json() == {"detail": f"Monitor with id {unknown_id} not found"}

    def test_without_token_returns_401(self, client):
        response = client.get("/monitors/1/stats")

        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}
