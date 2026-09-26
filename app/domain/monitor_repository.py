from app.domain.exceptions import MonitorNotFound
from app.domain.monitor import Monitor


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
        monitor = self._get_or_raise(monitor_id)
        del self.monitors[monitor.id]

    def list_all_monitors(self) -> list[Monitor]:
        return list(self.monitors.values())

    def update_monitor(self, monitor_id: int, payload: dict) -> Monitor:
        monitor = self._get_or_raise(monitor_id)
        for key, value in payload.items():
            setattr(monitor, key, value)
        return monitor
