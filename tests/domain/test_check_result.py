from datetime import datetime

from tests.domain.utils import create_check_result


class TestCheckResult:
    def setup_method(self):
        self.check_result = create_check_result()

    def test_check_result_stores_given_fields(self):
        assert self.check_result.monitor_id == 1
        assert self.check_result.checked_at == datetime(2026, 9, 26, 12, 0)
        assert self.check_result.is_up is True
        assert self.check_result.response_time_ms == 10

    def test_check_result_allows_missing_response_time(self):
        timeout_result = create_check_result(is_up=False, response_time_ms=None)

        assert timeout_result.response_time_ms is None
