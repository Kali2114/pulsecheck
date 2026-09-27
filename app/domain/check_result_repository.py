from app.domain.check_result import CheckResult


class InMemoryCheckResultRepository:
    def __init__(self) -> None:
        self.check_results: list[CheckResult] = []

    def add_check_result(self, check_result: CheckResult) -> None:
        self.check_results.append(check_result)

    def list_for_monitor(self, monitor_id: int) -> list[CheckResult]:
        return [
            result for result in self.check_results if result.monitor_id == monitor_id
        ]
