from app.domain.check_result import CheckResult


def uptime_percentage(results: list[CheckResult]) -> float | None:
    if not results:
        return None
    return sum(result.is_up for result in results) / len(results) * 100


def average_response_time(results: list[CheckResult]) -> float | None:
    response_times = [result.response_time_ms for result in results if result.is_up]
    if not response_times:
        return None
    return sum(response_times) / len(response_times)
