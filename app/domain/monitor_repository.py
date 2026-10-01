from typing import Any, Protocol, runtime_checkable

from app.domain.exceptions import MonitorNotFound
from app.domain.monitor import Monitor


@runtime_checkable
class MonitorRepository(Protocol):
    def add_monitor(self, monitor: Monitor) -> Monitor: ...

    def get_monitor(self, monitor_id: int) -> Monitor: ...

    def list_user_monitors(self, user_id: int) -> list[Monitor]: ...

    def list_all_monitors(self) -> list[Monitor]: ...

    def update_monitor(self, monitor_id: int, payload: dict[str, Any]) -> Monitor: ...

    def delete_monitor(self, monitor_id: int) -> None: ...


class InMemoryMonitorRepository:
    def __init__(self) -> None:
        self.monitors: dict[int, Monitor] = {}
        self._next_id = 1

    def add_monitor(self, monitor: Monitor) -> Monitor:
        monitor.id = self._next_id
        self._next_id += 1
        self.monitors[monitor.id] = monitor
        return monitor

    def _get_or_raise(self, monitor_id: int) -> Monitor:
        try:
            return self.monitors[monitor_id]
        except KeyError:
            raise MonitorNotFound(f"Monitor with id {monitor_id} not found.") from None

    def get_monitor(self, monitor_id: int) -> Monitor:
        return self._get_or_raise(monitor_id)

    def list_user_monitors(self, user_id: int) -> list[Monitor]:
        return [
            monitor for monitor in self.monitors.values() if monitor.user_id == user_id
        ]

    def delete_monitor(self, monitor_id: int) -> None:
        self._get_or_raise(monitor_id)
        del self.monitors[monitor_id]

    def list_all_monitors(self) -> list[Monitor]:
        return list(self.monitors.values())

    def update_monitor(self, monitor_id: int, payload: dict[str, Any]) -> Monitor:
        updated = self._get_or_raise(monitor_id).with_changes(payload)
        self.monitors[monitor_id] = updated
        return updated
