from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.exceptions import InvalidMonitorUpdate, MonitorNotFound
from app.domain.monitor import Monitor
from app.infrastructure.models import MonitorModel


class SQLAlchemyMonitorRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_monitor(self, monitor: Monitor) -> Monitor:
        model = MonitorModel(
            user_id=monitor.user_id,
            url=monitor.url,
            last_checked_at=monitor.last_checked_at,
            check_interval=monitor.check_interval,
            timeout=monitor.timeout,
            retry_count=monitor.retry_count,
        )
        self.session.add(model)
        self.session.flush()
        monitor.id = model.id
        return monitor

    def get_monitor(self, monitor_id: int) -> Monitor:
        return self._to_domain(self._get_model_or_raise(monitor_id))

    def list_user_monitors(self, user_id: int) -> list[Monitor]:
        statement = (
            select(MonitorModel)
            .where(MonitorModel.user_id == user_id)
            .order_by(MonitorModel.id)
        )
        models = self.session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def list_all_monitors(self) -> list[Monitor]:
        statement = select(MonitorModel).order_by(MonitorModel.id)
        models = self.session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def update_monitor(self, monitor_id: int, payload: dict[str, Any]) -> Monitor:
        model = self._get_model_or_raise(monitor_id)

        not_editable = set(payload) - Monitor.EDITABLE_FIELDS
        if not_editable:
            raise InvalidMonitorUpdate(
                f"Fields can't be updated: {', '.join(sorted(not_editable))}"
            )

        updated = self._to_domain(model, **payload)

        for key, value in payload.items():
            setattr(model, key, value)
        self.session.flush()
        return updated

    def _get_model_or_raise(self, monitor_id: int) -> MonitorModel:
        model = self.session.get(MonitorModel, monitor_id)
        if model is None:
            raise MonitorNotFound(f"Monitor {monitor_id} not found")
        return model

    @staticmethod
    def _to_domain(model: MonitorModel, **overrides: Any) -> Monitor:
        fields = {
            "id": model.id,
            "user_id": model.user_id,
            "url": model.url,
            "last_checked_at": model.last_checked_at,
            "check_interval": model.check_interval,
            "timeout": model.timeout,
            "retry_count": model.retry_count,
        }
        return Monitor(**(fields | overrides))
