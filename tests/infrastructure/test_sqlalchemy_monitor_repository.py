from datetime import UTC, datetime, timedelta

import pytest

from app.domain.exceptions import (
    InvalidMonitorUpdate,
    InvalidRetryCount,
    MonitorNotFound,
)
from app.domain.monitor import Monitor
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from tests.domain.utils import create_monitor


class TestSQLAlchemyMonitorRepository:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db_session = db_session
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

    def test_list_all_monitors_returns_monitors_of_all_users(self):
        monitor_1 = self.repository.add_monitor(self.monitor)
        monitor_2 = self.repository.add_monitor(create_monitor(user_id=2))
        monitor_3 = self.repository.add_monitor(create_monitor(user_id=3))

        results = self.repository.list_all_monitors()

        assert [monitor.id for monitor in results] == [
            monitor_1.id,
            monitor_2.id,
            monitor_3.id,
        ]

    def test_list_all_monitors_returns_empty_list_when_no_monitors_exist(self):
        results = self.repository.list_all_monitors()

        assert results == []

    def test_update_monitor_persists_changes(self):
        self.repository.add_monitor(self.monitor)
        payload = {
            "url": "https://example.com/updated",
            "last_checked_at": datetime(2026, 9, 30, 18, 0, tzinfo=UTC),
            "check_interval": timedelta(minutes=10),
            "timeout": 15,
            "retry_count": 5,
        }
        updated = self.repository.update_monitor(self.monitor.id, payload)
        self.db_session.expire_all()
        received = self.repository.get_monitor(self.monitor.id)

        assert isinstance(updated, Monitor)
        assert received.url == payload["url"]
        assert received.last_checked_at == payload["last_checked_at"]
        assert received.check_interval == payload["check_interval"]
        assert received.timeout == payload["timeout"]
        assert received.retry_count == payload["retry_count"]

    def test_update_monitor_raises_for_unknown_id(self):
        with pytest.raises(MonitorNotFound):
            self.repository.update_monitor(99, {})

    def test_update_monitor_with_invalid_value_leaves_monitor_unchanged(self):
        self.repository.add_monitor(self.monitor)

        with pytest.raises(InvalidRetryCount):
            self.repository.update_monitor(self.monitor.id, {"retry_count": 0})

        self.db_session.expire_all()
        received = self.repository.get_monitor(self.monitor.id)
        assert received.retry_count == self.monitor.retry_count

    @pytest.mark.parametrize("field", ["id", "user_id", "not_a_field"])
    def test_update_monitor_rejects_fields_that_are_not_editable(self, field):
        self.repository.add_monitor(self.monitor)

        with pytest.raises(InvalidMonitorUpdate):
            self.repository.update_monitor(self.monitor.id, {field: 2})

        self.db_session.expire_all()
        received = self.repository.get_monitor(self.monitor.id)
        assert received.id == self.monitor.id
        assert received.user_id == self.monitor.user_id
