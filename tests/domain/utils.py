from datetime import datetime, timedelta

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
