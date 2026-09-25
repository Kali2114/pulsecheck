from datetime import datetime, timedelta


class Monitor:
    def __init__(self, last_checked_at: datetime | None, check_interval: timedelta) -> None:
        self.last_checked_at = last_checked_at
        self.check_interval = check_interval

    def is_due(self, now) -> bool:
        if self.last_checked_at is None:
            return True
        elif self.last_checked_at + self.check_interval <= now:
            return True
        return False