from datetime import timedelta

from fastapi import APIRouter, Depends
from starlette import status

from app.api.dependencies import get_current_user, get_monitor_repository
from app.api.schemas import MonitorCreate, MonitorRead
from app.domain.monitor import Monitor
from app.domain.monitor_repository import MonitorRepository
from app.domain.user import User

monitors_router = APIRouter(
    prefix="/monitors",
    tags=["monitors"],
)


@monitors_router.post(
    "", response_model=MonitorRead, status_code=status.HTTP_201_CREATED
)
def create_monitor(
    payload: MonitorCreate,
    current_user: User = Depends(get_current_user),
    monitor_repository: MonitorRepository = Depends(get_monitor_repository),
) -> MonitorRead:
    monitor = _to_domain_monitor(payload, current_user.id)
    saved_monitor = monitor_repository.add_monitor(monitor)
    return _to_monitor_read(saved_monitor)


@monitors_router.get("", response_model=list[MonitorRead])
def list_monitors(
    current_user: User = Depends(get_current_user),
    monitor_repository: MonitorRepository = Depends(get_monitor_repository),
) -> list[MonitorRead]:
    monitors = monitor_repository.list_user_monitors(current_user.id)
    return [_to_monitor_read(m) for m in monitors]


def _to_domain_monitor(
    payload: MonitorCreate,
    user_id: int,
) -> Monitor:
    monitor = Monitor(
        url=payload.url,
        user_id=user_id,
        check_interval=timedelta(seconds=payload.check_interval_seconds),
        timeout=payload.timeout_seconds,
        retry_count=payload.retry_count,
        last_checked_at=None,
    )
    return monitor


def _to_monitor_read(monitor: Monitor) -> MonitorRead:
    return MonitorRead(
        id=monitor.id,
        url=monitor.url,
        check_interval_seconds=int(monitor.check_interval.total_seconds()),
        timeout_seconds=monitor.timeout,
        retry_count=monitor.retry_count,
        last_checked_at=monitor.last_checked_at,
    )
