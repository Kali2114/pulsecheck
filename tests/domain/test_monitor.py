from datetime import UTC, datetime, timedelta

import pytest

from app.domain.exceptions import InvalidMonitorUpdate, InvalidRetryCount
from app.domain.monitor import Monitor
from tests.domain.utils import create_monitor


class TestMonitor:
    def setup_method(self):
        self.check_interval = timedelta(minutes=5)
        self.url = "https://meetshift.org"
        self.user_id = 1

    def test_monitor_is_due_success(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        now = datetime(2026, 9, 25, 18, 5, tzinfo=UTC)
        monitor = Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

        assert monitor.is_due(now) is True

    def _make_monitor(self, last_checked_at: datetime | None) -> Monitor:
        return Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

    def _due_from(self, last_checked_at: datetime) -> datetime:
        return last_checked_at + self.check_interval - Monitor.DUE_TOLERANCE

    def test_monitor_is_due_within_tolerance(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        now = self._due_from(last_checked_at) + timedelta(milliseconds=1)

        monitor = self._make_monitor(last_checked_at)

        assert monitor.is_due(now) is True

    def test_monitor_is_due_at_tolerance_boundary(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        now = self._due_from(last_checked_at)

        monitor = self._make_monitor(last_checked_at)

        assert monitor.is_due(now) is True

    def test_monitor_is_not_due_outside_tolerance(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        now = self._due_from(last_checked_at) - timedelta(milliseconds=1)

        monitor = self._make_monitor(last_checked_at)

        assert monitor.is_due(now) is False

    def test_monitor_is_due_failure(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        now = datetime(2026, 9, 25, 18, 3, tzinfo=UTC)
        monitor = Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

        assert monitor.is_due(now) is False

    def test_monitor_is_due_last_check_none(self):
        last_checked_at = None
        now = datetime(2026, 9, 25, 18, 3, tzinfo=UTC)
        monitor = Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

        assert monitor.is_due(now) is True

    def test_monitor_is_due_well_past_interval(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        now = datetime(2026, 9, 25, 18, 25, tzinfo=UTC)
        monitor = Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

        assert monitor.is_due(now) is True

    def test_monitor_check_defaults(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        monitor = Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

        assert monitor.timeout == 5
        assert monitor.retry_count == 3

    def test_monitor_stores_url(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        monitor = Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

        assert monitor.url == self.url

    def test_monitor_stores_user_id(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        monitor = Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

        assert monitor.user_id == self.user_id

    def test_monitor_id_defaults_to_none(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        monitor = Monitor(self.user_id, self.url, last_checked_at, self.check_interval)

        assert monitor.id is None

    def test_monitor_stores_id(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0, tzinfo=UTC)
        monitor = Monitor(
            self.user_id, self.url, last_checked_at, self.check_interval, id=7
        )

        assert monitor.id == 7

    def test_monitor_rejects_retry_count_below_1(self):
        with pytest.raises(InvalidRetryCount):
            create_monitor(retry_count=0)

    def test_monitor_accepts_retry_count_of_1(self):
        monitor = create_monitor(retry_count=1)

        assert monitor.retry_count == 1

    def test_with_changes_returns_new_monitor_with_changes_applied(self):
        monitor = create_monitor(id=7)

        changed = monitor.with_changes({"url": "https://changed.example.com"})

        assert changed.url == "https://changed.example.com"
        assert changed.id == 7
        assert changed.user_id == monitor.user_id

    def test_with_changes_leaves_original_monitor_unchanged(self):
        monitor = create_monitor()

        monitor.with_changes({"url": "https://changed.example.com"})

        assert monitor.url == "http://example.com"

    @pytest.mark.parametrize("field", ["id", "user_id", "not_a_field"])
    def test_with_changes_rejects_fields_that_are_not_editable(self, field):
        with pytest.raises(InvalidMonitorUpdate):
            create_monitor().with_changes({field: 2})

    def test_with_changes_validates_new_values(self):
        with pytest.raises(InvalidRetryCount):
            create_monitor().with_changes({"retry_count": 0})
