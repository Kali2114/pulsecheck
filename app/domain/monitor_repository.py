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
