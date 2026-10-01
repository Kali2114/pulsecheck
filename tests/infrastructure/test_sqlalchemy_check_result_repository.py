from datetime import UTC, datetime, timedelta

import pytest

from app.domain.check_result import CheckResult
from app.infrastructure.check_result_repository import SQLAlchemyCheckResultRepository
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from tests.domain.utils import create_check_result, create_monitor


class TestSQLAlchemyCheckResultRepository:
    @pytest.fixture(autouse=True)
    def setup(self, db_session):
        self.db_session = db_session
        self.monitor_repository = SQLAlchemyMonitorRepository(db_session)
        self.check_result_repository = SQLAlchemyCheckResultRepository(db_session)
        self.monitor = create_monitor()
        self.monitor_repository.add_monitor(self.monitor)
        self.now = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)

    def _add_result(self, checked_at: datetime) -> CheckResult:
        check_result = create_check_result(
            monitor_id=self.monitor.id, checked_at=checked_at
        )
        self.check_result_repository.add_check_result(check_result)
        return check_result

    def test_add_check_result_persists_and_returns_it_for_monitor(self):
        check_result = self._add_result(self.now)

        self.db_session.expire_all()
        results = self.check_result_repository.list_for_monitor(self.monitor.id)

        assert len(results) == 1
        assert results[0].monitor_id == self.monitor.id
        assert results[0].checked_at == check_result.checked_at
        assert results[0].is_up == check_result.is_up
        assert results[0].response_time_ms == check_result.response_time_ms

    def test_list_for_monitor_excludes_results_before_since(self):
        since = self.now
        self._add_result(since - timedelta(minutes=1))
        newer_result = self._add_result(since + timedelta(minutes=1))

        self.db_session.expire_all()
        results = self.check_result_repository.list_for_monitor(
            self.monitor.id, since=since
        )

        assert [result.checked_at for result in results] == [newer_result.checked_at]

    def test_list_for_monitor_includes_result_at_since(self):
        since = self.now
        self._add_result(since)

        self.db_session.expire_all()
        results = self.check_result_repository.list_for_monitor(
            self.monitor.id, since=since
        )

        assert [result.checked_at for result in results] == [since]

    def test_list_for_monitor_returns_results_oldest_first(self):
        newer_time = self.now
        older_time = self.now - timedelta(hours=1)
        self._add_result(newer_time)
        self._add_result(older_time)

        self.db_session.expire_all()
        results = self.check_result_repository.list_for_monitor(self.monitor.id)

        assert [result.checked_at for result in results] == [older_time, newer_time]
