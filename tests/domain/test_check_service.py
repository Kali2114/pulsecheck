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

    def test_due_monitor_is_checked_and_result_is_stored(self):
        monitor = create_monitor(last_checked_at=None)
        self.monitor_repo.add_monitor(monitor)
        fake_pinger = FakePinger(
            PingResult(
                status_code=200,
                response_time_ms=120,
            )
        )
        now = datetime(2026, 9, 27, 22, 30)
        checker = CheckService(
            self.monitor_repo,
            self.check_result_repo,
            fake_pinger,
        )

        checker.check(now)

        stored_result = self.check_result_repo.get_latest(monitor.id)

        assert stored_result is not None
        assert stored_result.checked_at == now
        assert fake_pinger.calls == [(monitor.url, monitor.timeout)]
