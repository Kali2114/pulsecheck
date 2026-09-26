from datetime import datetime, timedelta

from app.domain.check_result import CheckResult
from app.domain.monitor import Monitor


def create_monitor(**kwargs) -> Monitor:
    payload = {
        "user_id": 1,
        "url": "http://example.com",
        "last_checked_at": datetime.now(),
        "check_interval": timedelta(seconds=5),
    }
    payload.update(kwargs)
    return Monitor(**payload)


def create_check_result(**kwargs) -> CheckResult:
    payload = {
        "monitor_id": 1,
        "checked_at": datetime(2026, 9, 26, 12, 0),
        "is_up": True,
        "response_time_ms": 10,
    }
    payload.update(kwargs)
    return CheckResult(**payload)
