from datetime import datetime

from app.domain.check_result_repository import InMemoryCheckResultRepository
from app.domain.check_service import CheckService
from app.domain.monitor_repository import InMemoryMonitorRepository
from app.domain.pinger import PingResult
from tests.domain.utils import create_monitor


class FakePinger:
    def __init__(self, result: PingResult) -> None:
        self.result = result
        self.calls: list[tuple[str, int]] = []

    def ping(self, url: str, timeout: int) -> PingResult:
        self.calls.append((url, timeout))
        return self.result


class TestCheckService:
    def setup_method(self):
        self.monitor_repo = InMemoryMonitorRepository()
        self.check_result_repo = InMemoryCheckResultRepository()
        self.monitor = create_monitor(last_checked_at=None)
        self.monitor_repo.add_monitor(self.monitor)
        self.now = datetime(2026, 9, 28, 12, 0)

    def _create_checker(self, ping_result: PingResult) -> CheckService:
        self.fake_pinger = FakePinger(ping_result)
        return CheckService(self.monitor_repo, self.check_result_repo, self.fake_pinger)

    def test_due_monitor_is_checked_and_result_is_stored(self):
        checker = self._create_checker(
            PingResult(status_code=200, response_time_ms=120)
        )

        checker.check(self.now)

        stored_result = self.check_result_repo.get_latest(self.monitor.id)

        assert stored_result is not None
        assert stored_result.checked_at == self.now
        assert self.fake_pinger.calls == [(self.monitor.url, self.monitor.timeout)]

    def test_timeout_stores_down_result_with_no_response_time(self):
        checker = self._create_checker(
            PingResult(status_code=None, response_time_ms=None)
        )

        checker.check(self.now)

        stored_result = self.check_result_repo.get_latest(self.monitor.id)

        assert stored_result is not None
        assert stored_result.is_up is False
        assert stored_result.response_time_ms is None
