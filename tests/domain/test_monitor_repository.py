from app.domain.monitor_repository import InMemoryMonitorRepository
from tests.domain.utils import create_monitor


class TestMonitorRepository:
    def setup_method(self) -> None:
        self.repository = InMemoryMonitorRepository()
        self.monitor = create_monitor()

    def test_add_monitor(self):
        added_monitor = self.repository.add_monitor(self.monitor)

        assert self.monitor is added_monitor
        assert self.monitor.id == 1

    def test_add_monitor_assigns_incrementing_id(self):
        self.repository.add_monitor(self.monitor)
        new_monitor = self.repository.add_monitor(create_monitor())

        assert new_monitor.id == 2
