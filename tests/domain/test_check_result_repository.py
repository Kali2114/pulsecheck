from datetime import timedelta

from app.domain.check_result_repository import (
    CheckResultRepository,
    InMemoryCheckResultRepository,
)
from tests.domain.utils import create_check_result


class TestCheckResultRepository:
    def setup_method(self):
        self.check_result = create_check_result()
        self.repository = InMemoryCheckResultRepository()
        self.repository.add_check_result(self.check_result)
        self.base_time = self.check_result.checked_at

    def test_list_for_monitor_returns_added_result(self):
        monitor_results = self.repository.list_for_monitor(self.check_result.monitor_id)

        assert len(monitor_results) == 1
        assert monitor_results[0] is self.check_result

    def test_list_for_monitor_excludes_other_monitors(self):
        self.repository.add_check_result(create_check_result(monitor_id=2))
        monitor_results = self.repository.list_for_monitor(self.check_result.monitor_id)

        assert len(monitor_results) == 1
        assert monitor_results[0] is self.check_result

    def test_list_for_monitor_excludes_results_before_since(self):
        since = self.check_result.checked_at + timedelta(minutes=1)
        newer_result = create_check_result(checked_at=since + timedelta(minutes=1))
        self.repository.add_check_result(newer_result)
        monitor_results = self.repository.list_for_monitor(
            self.check_result.monitor_id, since=since
        )

        assert monitor_results == [newer_result]

    def test_list_for_monitor_includes_result_exactly_at_since(self):
        since = self.check_result.checked_at
        monitor_results = self.repository.list_for_monitor(
            self.check_result.monitor_id, since=since
        )

        assert monitor_results == [self.check_result]

    def test_list_for_monitor_applies_since_only_to_given_monitor(self):
        since = self.check_result.checked_at
        other_monitor_result = create_check_result(
            monitor_id=2, checked_at=since + timedelta(minutes=1)
        )
        self.repository.add_check_result(other_monitor_result)
        monitor_results = self.repository.list_for_monitor(
            self.check_result.monitor_id, since=since
        )

        assert monitor_results == [self.check_result]

    def test_list_for_monitor_returns_results_oldest_first(self):
        newest_result = create_check_result(
            checked_at=self.check_result.checked_at + timedelta(minutes=2)
        )
        oldest_result = create_check_result(
            checked_at=self.check_result.checked_at - timedelta(minutes=2)
        )
        self.repository.add_check_result(newest_result)
        self.repository.add_check_result(oldest_result)
        monitor_results = self.repository.list_for_monitor(self.check_result.monitor_id)

        assert monitor_results == [oldest_result, self.check_result, newest_result]

    def test_get_latest_returns_newest_result(self):
        newest_result = create_check_result(
            checked_at=self.check_result.checked_at + timedelta(minutes=2)
        )
        oldest_result = create_check_result(
            checked_at=self.check_result.checked_at - timedelta(minutes=2)
        )
        self.repository.add_check_result(newest_result)
        self.repository.add_check_result(oldest_result)
        latest_result = self.repository.get_latest(self.check_result.monitor_id)

        assert latest_result is newest_result

    def test_get_latest_returns_none_for_monitor_without_results(self):
        assert self.repository.get_latest(99) is None

    def test_get_latest_for_monitors_returns_latest_result_per_monitor(self):
        first_check_old = create_check_result(
            monitor_id=10, checked_at=self.base_time - timedelta(minutes=5)
        )
        first_check_new = create_check_result(
            monitor_id=10, checked_at=self.base_time + timedelta(minutes=5)
        )
        second_check_old = create_check_result(
            monitor_id=20, checked_at=self.base_time - timedelta(minutes=5)
        )
        second_check_new = create_check_result(
            monitor_id=20, checked_at=self.base_time + timedelta(minutes=5)
        )
        checks = [second_check_new, first_check_new, second_check_old, first_check_old]
        for check in checks:
            self.repository.add_check_result(check)

        results = self.repository.get_latest_for_monitors([10, 20])

        assert len(results) == 2
        assert results[10].checked_at == first_check_new.checked_at
        assert results[20].checked_at == second_check_new.checked_at

    def test_get_latest_for_monitors_returns_only_requested_monitors(self):
        check_in = create_check_result(
            monitor_id=10, checked_at=self.base_time + timedelta(minutes=5)
        )
        check_out = create_check_result(
            monitor_id=20, checked_at=self.base_time + timedelta(minutes=10)
        )
        self.repository.add_check_result(check_in)
        self.repository.add_check_result(check_out)

        results = self.repository.get_latest_for_monitors([10])

        assert set(results.keys()) == {10}

    def test_get_latest_for_monitors_leaves_out_monitors_without_results(self):
        check = create_check_result(
            monitor_id=20, checked_at=self.base_time + timedelta(minutes=5)
        )
        self.repository.add_check_result(check)

        results = self.repository.get_latest_for_monitors([10, 20])

        assert set(results.keys()) == {20}

    def test_get_latest_for_monitors_returns_empty_dict_when_no_ids(self):
        results = self.repository.get_latest_for_monitors([])

        assert results == {}

    def test_in_memory_repository_satisfies_check_result_repository_protocol(self):
        assert isinstance(self.repository, CheckResultRepository)
