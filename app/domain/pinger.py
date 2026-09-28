from dataclasses import dataclass
from typing import Protocol


@dataclass
class PingResult:
    status_code: int | None
    response_time_ms: int | None

    def is_up(self) -> bool:
        if self.status_code is None:
            return False
        return 200 <= self.status_code < 400


class Pinger(Protocol):
    def ping(self, url: str, timeout: int) -> PingResult: ...
