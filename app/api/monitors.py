from datetime import timedelta

from fastapi import APIRouter, Depends
from starlette import status

from app.api.dependencies import (
    get_current_user,
    get_current_user_monitor,
    get_monitor_repository,
)
from app.api.schemas import MonitorCreate, MonitorRead, MonitorUpdate
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


@monitors_router.get("/{monitor_id}", response_model=MonitorRead)
def get_monitor(
    current_monitor: Monitor = Depends(get_current_user_monitor),
) -> MonitorRead:
    return _to_monitor_read(current_monitor)


@monitors_router.patch("/{monitor_id}", response_model=MonitorRead)
def update_monitor(
    payload: MonitorUpdate,
    repository: MonitorRepository = Depends(get_monitor_repository),
    current_monitor: Monitor = Depends(get_current_user_monitor),
) -> MonitorRead:
    changes = payload.model_dump(exclude_unset=True)
    domain_changes = _to_domain_changes(changes)
    updated_monitor = repository.update_monitor(current_monitor.id, domain_changes)
    return _to_monitor_read(updated_monitor)


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


def _to_domain_changes(changes: dict) -> dict:
    domain_changes = {}

    if "url" in changes:
        domain_changes["url"] = changes["url"]

    if "retry_count" in changes:
        domain_changes["retry_count"] = changes["retry_count"]

    if "timeout_seconds" in changes:
        domain_changes["timeout"] = changes["timeout_seconds"]

    if "check_interval_seconds" in changes:
        domain_changes["check_interval"] = timedelta(
            seconds=changes["check_interval_seconds"]
        )

    return domain_changes


def _to_monitor_read(monitor: Monitor) -> MonitorRead:
    return MonitorRead(
        id=monitor.id,
        url=monitor.url,
        check_interval_seconds=int(monitor.check_interval.total_seconds()),
        timeout_seconds=monitor.timeout,
        retry_count=monitor.retry_count,
        last_checked_at=monitor.last_checked_at,
    )
