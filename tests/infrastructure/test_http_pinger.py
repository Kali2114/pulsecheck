import httpx
import pytest

from app.domain.pinger import Pinger
from app.infrastructure.http_pinger import HttpPinger


@pytest.fixture
def make_pinger():
    clients = []

    def _make_pinger(handler):
        transport = httpx.MockTransport(handler)
        client = httpx.Client(transport=transport)
        clients.append(client)
        return HttpPinger(client)

    yield _make_pinger

    for client in clients:
        client.close()


class TestHttpPinger:

    def test_ping_returns_successful_result(self, make_pinger):
        def handler(request):
            return httpx.Response(200)

        pinger = make_pinger(handler)

        result = pinger.ping("http://example.com", timeout=5)

        assert result.status_code == 200
        assert result.response_time_ms is not None
        assert result.is_up()

    def test_ping_keeps_response_time_on_server_error(self, make_pinger):
        def handler(request):
            return httpx.Response(500)

        pinger = make_pinger(handler)

        result = pinger.ping("http://example.com", timeout=5)

        assert result.status_code == 500
        assert result.response_time_ms is not None
        assert not result.is_up()

    def test_ping_follows_redirect_to_final_status(self, make_pinger):
        def handler(request):
            if request.url.path == "/":
                return httpx.Response(
                    301,
                    headers={"Location": "http://example.com/final"},
                )
            if request.url.path == "/final":
                return httpx.Response(200)
            return httpx.Response(404)

        pinger = make_pinger(handler)

        result = pinger.ping("http://example.com", timeout=5)

        assert result.status_code == 200
        assert result.is_up()

    def test_ping_returns_none_when_timeout(self, make_pinger):
        def handler(request):
            raise httpx.ReadTimeout("timeout")

        pinger = make_pinger(handler)

        result = pinger.ping("http://example.com", timeout=5)

        assert result.status_code is None
        assert not result.is_up()
        assert result.response_time_ms is None

    def test_ping_returns_none_when_connection_failed(self, make_pinger):
        def handler(request):
            raise httpx.ConnectError("connection failed")

        pinger = make_pinger(handler)

        result = pinger.ping("http://example.com", timeout=5)

        assert result.status_code is None
        assert not result.is_up()
        assert result.response_time_ms is None

    def test_ping_returns_down_for_invalid_url(self, make_pinger):
        def handler(request):
            raise AssertionError("an invalid URL should never reach the transport")

        pinger = make_pinger(handler)

        result = pinger.ping("http://[::1", timeout=5)

        assert result.status_code is None
        assert result.response_time_ms is None
        assert not result.is_up()

    def test_http_pinger_satisfies_pinger_protocol(self, make_pinger):
        pinger = make_pinger(lambda request: httpx.Response(200))

        assert isinstance(pinger, Pinger)
