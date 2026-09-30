from datetime import datetime

from app.domain.check_result import CheckResult
from app.domain.check_result_repository import CheckResultRepository
from app.domain.monitor import Monitor
from app.domain.monitor_repository import MonitorRepository
from app.domain.pinger import Pinger, PingResult


class CheckService:
    def __init__(
        self,
        monitor_repo: MonitorRepository,
        check_result_repo: CheckResultRepository,
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
            if monitor.id is None:
                continue
            ping_result = self._ping_with_retries(monitor)

            check_result = CheckResult(
                monitor_id=monitor.id,
                checked_at=now,
                is_up=ping_result.is_up(),
                response_time_ms=ping_result.response_time_ms,
            )

            self.check_result_repo.add_check_result(check_result)
            self.monitor_repo.update_monitor(monitor.id, {"last_checked_at": now})

    def _ping_with_retries(self, monitor: Monitor) -> PingResult:
        # retry_count is the total number of attempts (>= 1, enforced by Monitor).
        ping_result = self.pinger.ping(monitor.url, monitor.timeout)
        for _ in range(monitor.retry_count - 1):
            if ping_result.is_up():
                break
            ping_result = self.pinger.ping(monitor.url, monitor.timeout)
        return ping_result
