from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.check_result import CheckResult


@runtime_checkable
class CheckResultRepository(Protocol):
    """What the domain needs from check result storage (see MonitorRepository)."""

    def add_check_result(self, check_result: CheckResult) -> None: ...

    def list_for_monitor(
        self, monitor_id: int, since: datetime | None = None
    ) -> list[CheckResult]: ...

    def get_latest(self, monitor_id: int) -> CheckResult | None: ...


class InMemoryCheckResultRepository:
    def __init__(self) -> None:
        self.check_results: list[CheckResult] = []

    def add_check_result(self, check_result: CheckResult) -> None:
        self.check_results.append(check_result)

    def _results_for_monitor(self, monitor_id: int) -> list[CheckResult]:
        return [
            result for result in self.check_results if result.monitor_id == monitor_id
        ]

    def list_for_monitor(
        self, monitor_id: int, since: datetime | None = None
    ) -> list[CheckResult]:
        monitor_results = self._results_for_monitor(monitor_id)
        if since is not None:
            monitor_results = [
                result for result in monitor_results if result.checked_at >= since
            ]
        return sorted(monitor_results, key=lambda result: result.checked_at)

    def get_latest(self, monitor_id: int) -> CheckResult | None:
        monitor_results = self._results_for_monitor(monitor_id)
        return max(monitor_results, key=lambda result: result.checked_at, default=None)
