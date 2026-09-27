from datetime import datetime

from app.domain.check_result import CheckResult
from app.domain.check_result_repository import InMemoryCheckResultRepository
from app.domain.monitor_repository import InMemoryMonitorRepository
from app.domain.pinger import Pinger


class CheckService:
    def __init__(
        self,
        monitor_repo: InMemoryMonitorRepository,
        check_result_repo: InMemoryCheckResultRepository,
        pinger: Pinger,
    ) -> None:
        self.monitor_repo = monitor_repo
        self.check_result_repo = check_result_repo
        self.pinger = pinger

    def check(self, now: datetime) -> None:
        monitors = [
            monitor
            for monitor in self.monitor_repo.list_all_monitors()
            if monitor.is_due(now)
        ]
        for monitor in monitors:
            ping_result = self.pinger.ping(
                monitor.url,
                monitor.timeout,
            )

            check_result = CheckResult(
                monitor_id=monitor.id,
                checked_at=now,
                is_up=200 <= ping_result.status_code < 400,
                response_time_ms=ping_result.response_time_ms,
            )

            self.check_result_repo.add_check_result(check_result)
