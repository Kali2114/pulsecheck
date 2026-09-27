from dataclasses import dataclass
from typing import Protocol


@dataclass
class PingResult:
    status_code: int | None
    response_time_ms: int | None


class Pinger(Protocol):
    def ping(self, url: str, timeout: int) -> PingResult: ...
