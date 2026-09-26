import pytest

from app.domain.exceptions import MonitorNotFound
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

    def test_get_monitor(self):
        added_monitor = self.repository.add_monitor(self.monitor)
        received_monitor = self.repository.get_monitor(added_monitor.id)

        assert added_monitor is received_monitor

    def test_get_monitor_not_found(self):
        with pytest.raises(MonitorNotFound):
            self.repository.get_monitor(99)

    def test_list_user_monitor(self):
        self.repository.add_monitor(self.monitor)
        self.repository.add_monitor(create_monitor())
        self.repository.add_monitor(create_monitor(user_id=2))
        result = self.repository.list_user_monitors(1)

        assert len(result) == 2
        assert [x.user_id for x in result] == [1, 1]

    def test_list_user_monitor_empty_list(self):
        result = self.repository.list_user_monitors(1)

        assert result == []

    def test_delete_user_monitor(self):
        self.repository.add_monitor(self.monitor)
        self.repository.delete_monitor(self.monitor.id)

        with pytest.raises(MonitorNotFound):
            self.repository.get_monitor(self.monitor.id)

    def test_delete_user_monitor_not_found(self):
        with pytest.raises(MonitorNotFound):
            self.repository.delete_monitor(99)

    def test_list_all_monitors(self):
        self.repository.add_monitor(self.monitor)
        self.repository.add_monitor(create_monitor(url="https://test2.example.com"))
        self.repository.add_monitor(create_monitor(url="https://test3.example.com"))
        self.repository.add_monitor(
            create_monitor(url="https://test4.example.com", user_id=2)
        )
        self.repository.add_monitor(
            create_monitor(url="https://test5.example.com", user_id=3)
        )
        result = self.repository.list_all_monitors()

        assert len(result) == 5
        assert sorted(x.user_id for x in result) == [1, 1, 1, 2, 3]
