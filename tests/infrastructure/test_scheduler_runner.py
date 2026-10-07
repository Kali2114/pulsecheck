import pytest

from app.infrastructure import scheduler_runner
from app.infrastructure.database import SessionLocal
from app.infrastructure.http_pinger import HttpPinger
from app.infrastructure.scheduler import create_scheduler


@pytest.fixture
def captured_create_scheduler(monkeypatch):
    # Wrap the real create_scheduler: record what start_scheduler passes in, and
    # use an hour-long interval so the job never fires (against the dev DB, with
    # real HTTP) while the test runs.
    captured = {}

    def wrapper(session_factory, pinger):
        captured["session_factory"] = session_factory
        captured["pinger"] = pinger
        return create_scheduler(session_factory, pinger, interval_seconds=3600)

    monkeypatch.setattr(scheduler_runner, "create_scheduler", wrapper)
    return captured


class TestSchedulerRunner:
    def test_start_wires_real_dependencies_and_starts_scheduler(
        self, captured_create_scheduler
    ):
        scheduler, client = scheduler_runner.start_scheduler()

        try:
            assert scheduler.running
            assert captured_create_scheduler["session_factory"] is SessionLocal
            pinger = captured_create_scheduler["pinger"]
            assert isinstance(pinger, HttpPinger)
            assert pinger.client is client
        finally:
            scheduler_runner.stop_scheduler(scheduler, client)

    def test_stop_shuts_down_scheduler_and_closes_client(
        self, captured_create_scheduler
    ):
        scheduler, client = scheduler_runner.start_scheduler()

        scheduler_runner.stop_scheduler(scheduler, client)

        assert not scheduler.running
        assert client.is_closed
