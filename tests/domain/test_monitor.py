from datetime import datetime, timedelta
from app.domain.monitor import Monitor


class TestMonitor:
    def setup_method(self):
        self.check_interval = timedelta(minutes=5)
        self.url = "https://meetshift.org"

    def test_monitor_is_due_success(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0)
        now = datetime(2026, 9, 25, 18, 5)
        monitor = Monitor(self.url, last_checked_at, self.check_interval)

        assert monitor.is_due(now) is True

    def test_monitor_is_due_failure(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0)
        now = datetime(2026, 9, 25, 18, 3)
        monitor = Monitor(self.url, last_checked_at, self.check_interval)

        assert monitor.is_due(now) is False

    def test_monitor_is_due_last_check_none(self):
        last_checked_at = None
        now = datetime(2026, 9, 25, 18, 3)
        monitor = Monitor(self.url, last_checked_at, self.check_interval)

        assert monitor.is_due(now) is True

    def test_monitor_is_due_well_past_interval(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0)
        now = datetime(2026, 9, 25, 18, 25)
        monitor = Monitor(self.url, last_checked_at, self.check_interval)

        assert monitor.is_due(now) is True

    def test_monitor_check_defaults(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0)
        monitor = Monitor(self.url, last_checked_at, self.check_interval)

        assert monitor.timeout == 5
        assert monitor.retry_count == 3

    def test_monitor_stores_url(self):
        last_checked_at = datetime(2026, 9, 25, 18, 0)
        monitor = Monitor(self.url, last_checked_at, self.check_interval)

        assert monitor.url == self.url