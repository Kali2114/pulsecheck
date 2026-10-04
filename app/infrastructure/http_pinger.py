import time

import httpx

from app.domain.pinger import PingResult


class HttpPinger:
    def __init__(self, client: httpx.Client) -> None:
        self.client = client

    def ping(self, url: str, timeout: int) -> PingResult:
        start = time.perf_counter()
        try:
            response = self.client.get(url, timeout=timeout, follow_redirects=True)
        except (httpx.RequestError, httpx.InvalidURL):
            return PingResult(
                status_code=None,
                response_time_ms=None,
            )
        elapsed = time.perf_counter() - start
        return PingResult(
            status_code=response.status_code, response_time_ms=int(elapsed * 1000)
        )
