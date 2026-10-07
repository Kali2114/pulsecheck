from datetime import datetime, timedelta
from typing import Any

from app.domain.exceptions import InvalidMonitorUpdate, InvalidRetryCount


class Monitor:
    DUE_TOLERANCE = timedelta(seconds=1)
    EDITABLE_FIELDS = frozenset(
        {"url", "last_checked_at", "check_interval", "timeout", "retry_count"}
    )

    def __init__(
        self,
        user_id: int,
        url: str,
        last_checked_at: datetime | None,
        check_interval: timedelta,
        timeout: int = 5,
        retry_count: int = 3,
        id: int | None = None,
    ) -> None:
        if retry_count < 1:
            raise InvalidRetryCount(f"Invalid retry count {retry_count}")
        self.id = id
        self.user_id = user_id
        self.url = url
        self.last_checked_at = last_checked_at
        self.check_interval = check_interval
        self.timeout = timeout
        self.retry_count = retry_count

    def with_changes(self, changes: dict[str, Any]) -> "Monitor":
        """Return a new, validated Monitor with `changes` applied.

        Raises InvalidMonitorUpdate for fields outside EDITABLE_FIELDS, and the
        constructor's own errors (e.g. InvalidRetryCount) for invalid values.
        The original monitor is never modified.
        """
        not_editable = set(changes) - self.EDITABLE_FIELDS
        if not_editable:
            raise InvalidMonitorUpdate(
                f"Fields can't be updated: {', '.join(sorted(not_editable))}"
            )
        fields = {
            "id": self.id,
            "user_id": self.user_id,
            "url": self.url,
            "last_checked_at": self.last_checked_at,
            "check_interval": self.check_interval,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
        }
        return Monitor(**(fields | changes))

    def is_due(self, now: datetime) -> bool:
        if self.last_checked_at is None:
            return True
        due_from = self.last_checked_at + self.check_interval - self.DUE_TOLERANCE

        return due_from <= now
