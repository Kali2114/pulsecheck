from datetime import UTC, datetime

import pytest

from app.domain.exceptions import MonitorNotFound
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from tests.domain.utils import create_monitor


class TestSQLAlchemyMonitorRepository:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.monitor = create_monitor()
        self.repository = SQLAlchemyMonitorRepository(db_session)

    def test_add_monitor_assigns_id(self):
        self.repository.add_monitor(self.monitor)

        received = self.repository.get_monitor(self.monitor.id)

        assert received.id is not None

    def test_get_monitor_returns_all_fields(self):
        self.repository.add_monitor(self.monitor)

        received = self.repository.get_monitor(self.monitor.id)

        assert received.url == self.monitor.url
        assert received.user_id == self.monitor.user_id
        assert received.timeout == self.monitor.timeout
        assert received.last_checked_at == self.monitor.last_checked_at
        assert received.check_interval == self.monitor.check_interval
        assert received.retry_count == self.monitor.retry_count

    def test_get_monitor_raises_for_unknown_id(self):
        with pytest.raises(MonitorNotFound):
            self.repository.get_monitor(99)

    def test_get_monitor_preserves_utc_last_checked_at(self):
        monitor = create_monitor(
            last_checked_at=datetime(2026, 9, 30, 12, 0, tzinfo=UTC)
        )
        self.repository.add_monitor(monitor)

        received = self.repository.get_monitor(monitor.id)

        assert received.last_checked_at == monitor.last_checked_at

    def test_list_user_monitors_returns_only_given_users_monitors(self):
        monitor_1 = self.monitor
        monitor_2 = create_monitor()
        monitor_3 = create_monitor()
        other_user_monitor = create_monitor(user_id=2)

        self.repository.add_monitor(monitor_1)
        self.repository.add_monitor(monitor_2)
        self.repository.add_monitor(monitor_3)
        self.repository.add_monitor(other_user_monitor)

        results = self.repository.list_user_monitors(self.monitor.user_id)

        assert [monitor.id for monitor in results] == [
            monitor_1.id,
            monitor_2.id,
            monitor_3.id,
        ]

    def test_list_user_monitors_returns_empty_list_when_user_has_no_monitors(self):
        results = self.repository.list_user_monitors(999)

        assert results == []
