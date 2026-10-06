from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from app.domain.check_service import CheckService
from app.domain.pinger import Pinger
from app.infrastructure.check_result_repository import SQLAlchemyCheckResultRepository
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository


def run_check(
    session_factory: sessionmaker[Session],
    pinger: Pinger,
    now: datetime,
) -> None:
    session = session_factory()
    monitor_repository = SQLAlchemyMonitorRepository(session)
    check_result_repository = SQLAlchemyCheckResultRepository(session)
    check_service = CheckService(
        monitor_repo=monitor_repository,
        check_result_repo=check_result_repository,
        pinger=pinger,
    )
    try:
        check_service.check(now)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
