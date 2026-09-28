from app.domain.pinger import PingResult


class TestPingResult:

    def test_is_up_false_without_status_code(self):
        ping_result = PingResult(
            status_code=None,
            response_time_ms=None,
        )

        assert ping_result.is_up() is False

    def test_is_up_false_below_2xx(self):
        ping_result = PingResult(
            status_code=199,
            response_time_ms=None,
        )

        assert ping_result.is_up() is False

    def test_is_up_true_for_2xx(self):
        ping_result = PingResult(
            status_code=200,
            response_time_ms=None,
        )

        assert ping_result.is_up() is True

    def test_is_up_true_for_3xx(self):
        ping_result = PingResult(
            status_code=399,
            response_time_ms=None,
        )

        assert ping_result.is_up() is True

    def test_is_up_false_for_4xx(self):
        ping_result = PingResult(
            status_code=400,
            response_time_ms=None,
        )

        assert ping_result.is_up() is False

    def test_is_up_false_for_5xx(self):
        ping_result = PingResult(
            status_code=500,
            response_time_ms=10,
        )

        assert ping_result.is_up() is False
