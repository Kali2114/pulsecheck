from datetime import UTC, datetime

from app.domain.check_result_repository import InMemoryCheckResultRepository
from app.domain.check_service import CheckService
from app.domain.monitor_repository import InMemoryMonitorRepository
from app.domain.pinger import PingResult
from tests.domain.utils import create_monitor


class FakePinger:
    def __init__(self, results: list[PingResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def ping(self, url: str, timeout: int) -> PingResult:
        self.calls.append((url, timeout))
        attempt = min(len(self.calls), len(self.results)) - 1
        return self.results[attempt]


class TestCheckService:
    def setup_method(self):
        self.monitor_repo = InMemoryMonitorRepository()
        self.check_result_repo = InMemoryCheckResultRepository()
        self.monitor = create_monitor(last_checked_at=None)
        self.monitor_repo.add_monitor(self.monitor)
        self.now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)

    def _create_checker(self, *ping_results: PingResult) -> CheckService:
        self.fake_pinger = FakePinger(list(ping_results))
        return CheckService(
            self.monitor_repo,
            self.check_result_repo,
            self.fake_pinger,
        )

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

    def test_500_stores_down_result_with_response_time(self):
        checker = self._create_checker(PingResult(status_code=500, response_time_ms=50))

        checker.check(self.now)

        stored_result = self.check_result_repo.get_latest(self.monitor.id)

        assert stored_result is not None
        assert stored_result.is_up is False
        assert stored_result.response_time_ms == 50

    def test_check_updates_monitor_last_checked_at(self):
        checker = self._create_checker(
            PingResult(status_code=200, response_time_ms=120)
        )

        checker.check(self.now)

        updated_monitor = self.monitor_repo.get_monitor(self.monitor.id)

        assert updated_monitor.last_checked_at == self.now

    def test_monitor_without_id_is_skipped(self):
        checker = self._create_checker(
            PingResult(status_code=200, response_time_ms=120)
        )
        self.monitor.id = None

        checker.check(self.now)

        assert self.fake_pinger.calls == []
        assert self.check_result_repo.check_results == []

    def test_retry_succeeds_on_second_attempt(self):
        self.monitor.retry_count = 2
        checker = self._create_checker(
            PingResult(status_code=500, response_time_ms=120),
            PingResult(status_code=200, response_time_ms=50),
        )

        checker.check(self.now)

        results = self.check_result_repo.list_for_monitor(self.monitor.id)

        assert len(self.fake_pinger.calls) == 2
        assert len(results) == 1
        assert results[0].is_up is True
        assert results[0].response_time_ms == 50

    def test_all_attempts_fail_stores_one_down_result(self):
        self.monitor.retry_count = 4
        checker = self._create_checker(
            PingResult(status_code=500, response_time_ms=120),
        )
        checker.check(self.now)
        results = self.check_result_repo.list_for_monitor(self.monitor.id)

        assert len(self.fake_pinger.calls) == 4
        assert len(results) == 1
        assert results[0].is_up is False
