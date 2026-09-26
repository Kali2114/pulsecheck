from datetime import datetime

from tests.domain.utils import create_check_result


class TestCheckResult:

    def test_check_result(self):
        check_result = create_check_result()

        assert check_result.monitor_id == 1
        assert check_result.checked_at == datetime(2026, 9, 26, 12, 0)
        assert check_result.is_up is True
        assert check_result.response_time_ms == 10
