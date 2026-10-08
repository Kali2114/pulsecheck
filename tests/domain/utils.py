from datetime import UTC, datetime, timedelta

from app.domain.check_result import CheckResult
from app.domain.monitor import Monitor
from app.domain.user import User


def create_monitor(**kwargs) -> Monitor:
    payload = {
        "user_id": 1,
        "url": "http://example.com",
        "last_checked_at": None,
        "check_interval": timedelta(seconds=5),
    }
    payload.update(kwargs)
    return Monitor(**payload)


def create_check_result(**kwargs) -> CheckResult:
    payload = {
        "monitor_id": 1,
        "checked_at": datetime(2026, 9, 26, 12, 0, tzinfo=UTC),
        "is_up": True,
        "response_time_ms": 10,
    }
    payload.update(kwargs)
    return CheckResult(**payload)


def create_user(**kwargs) -> User:
    payload = {
        "email": "user@example.com",
        "hashed_password": "hashed:secret123",
        "id": None,
    }
    payload.update(kwargs)
    return User(**payload)
