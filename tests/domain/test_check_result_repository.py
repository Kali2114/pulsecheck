from app.domain.check_result_repository import InMemoryCheckResultRepository
from tests.domain.utils import create_check_result


class TestCheckResultRepository:
    def setup_method(self):
        self.check_result = create_check_result()
        self.repository = InMemoryCheckResultRepository()
        self.repository.add_check_result(self.check_result)

    def test_list_for_monitor_returns_added_result(self):
        monitor_results = self.repository.list_for_monitor(self.check_result.monitor_id)

        assert len(monitor_results) == 1
        assert monitor_results[0] is self.check_result

    def test_list_for_monitor_excludes_other_monitors(self):
        self.repository.add_check_result(create_check_result(monitor_id=2))
        monitor_results = self.repository.list_for_monitor(self.check_result.monitor_id)

        assert len(monitor_results) == 1
        assert monitor_results[0] is self.check_result
