from datetime import UTC, datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session, sessionmaker

from app.domain.pinger import Pinger
from app.infrastructure.check_runner import run_check

CHECK_INTERVAL_SECONDS = 10


def create_scheduler(
    session_factory: sessionmaker[Session],
    pinger: Pinger,
    interval_seconds: int = CHECK_INTERVAL_SECONDS,
) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    def scheduled_check() -> None:
        run_check(
            session_factory=session_factory,
            pinger=pinger,
            now=datetime.now(UTC),
        )

    scheduler.add_job(
        scheduled_check,
        trigger="interval",
        seconds=interval_seconds,
        max_instances=1,
        coalesce=True,
    )

    return scheduler
