from datetime import datetime


class CheckResult:
    def __init__(
        self, monitor_id: int, checked_at: datetime, is_up: bool, response_time_ms: int
    ) -> None:
        self.monitor_id = monitor_id
        self.checked_at = checked_at
        self.is_up = is_up
        self.response_time_ms = response_time_ms
