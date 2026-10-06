import httpx
from apscheduler.schedulers.background import BackgroundScheduler

from app.infrastructure.database import SessionLocal
from app.infrastructure.http_pinger import HttpPinger
from app.infrastructure.scheduler import create_scheduler


def start_scheduler() -> tuple[BackgroundScheduler, httpx.Client]:
    client = httpx.Client()
    pinger = HttpPinger(client)

    scheduler = create_scheduler(
        session_factory=SessionLocal,
        pinger=pinger,
    )

    scheduler.start()

    return scheduler, client


def stop_scheduler(scheduler: BackgroundScheduler, client: httpx.Client) -> None:
    scheduler.shutdown()
    client.close()
