from datetime import datetime, timedelta


class Monitor:
    def __init__(self, url: str, last_checked_at: datetime | None, check_interval: timedelta, timeout: int = 5, retry_count: int = 3) -> None:
        self.url = url
        self.last_checked_at = last_checked_at
        self.check_interval = check_interval
        self.timeout = timeout
        self.retry_count = retry_count

    def is_due(self, now: datetime) -> bool:
        if self.last_checked_at is None:
            return True
        if self.last_checked_at + self.check_interval <= now:
            return True
        return False