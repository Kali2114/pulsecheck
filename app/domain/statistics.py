from app.domain.check_result import CheckResult


def uptime_percentage(results: list[CheckResult]) -> float | None:
    if not results:
        return None
    return sum(check_result.is_up for check_result in results) / len(results) * 100
