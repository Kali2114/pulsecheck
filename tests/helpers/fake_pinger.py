from app.domain.pinger import PingResult


class FakePinger:
    def __init__(
        self,
        result: PingResult,
        failing_urls: set[str] | None = None,
    ) -> None:
        self.result = result
        self.failing_urls = failing_urls or set()

    def ping(self, url: str, timeout: int) -> PingResult:
        if url in self.failing_urls:
            raise RuntimeError("boom")

        return self.result
