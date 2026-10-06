from fastapi.testclient import TestClient

import app.main
from app.config import settings


def test_tests_run_with_scheduler_disabled():
    assert settings.scheduler_enabled is False


def test_lifespan_does_not_start_scheduler_when_disabled(monkeypatch):
    def fail_if_called():
        raise AssertionError("scheduler must not start when disabled")

    monkeypatch.setattr(app.main, "start_scheduler", fail_if_called)

    with TestClient(app.main.app):
        pass


def test_lifespan_starts_and_stops_scheduler_when_enabled(monkeypatch):
    calls = []
    scheduler, client = object(), object()

    def fake_start():
        calls.append("start")
        return scheduler, client

    def fake_stop(stopped_scheduler, closed_client):
        assert stopped_scheduler is scheduler
        assert closed_client is client
        calls.append("stop")

    monkeypatch.setattr(settings, "scheduler_enabled", True)
    monkeypatch.setattr(app.main, "start_scheduler", fake_start)
    monkeypatch.setattr(app.main, "stop_scheduler", fake_stop)

    with TestClient(app.main.app):
        assert calls == ["start"]

    assert calls == ["start", "stop"]
