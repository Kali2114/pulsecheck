from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.check_result import CheckResult
from app.infrastructure.models import CheckResultModel


class SQLAlchemyCheckResultRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_check_result(self, check_result: CheckResult) -> None:
        model = CheckResultModel(
            monitor_id=check_result.monitor_id,
            checked_at=check_result.checked_at,
            is_up=check_result.is_up,
            response_time_ms=check_result.response_time_ms,
        )
        self.session.add(model)
        self.session.flush()

    def list_for_monitor(
        self, monitor_id: int, since: datetime | None = None
    ) -> list[CheckResult]:
        statement = (
            select(CheckResultModel)
            .where(CheckResultModel.monitor_id == monitor_id)
            .order_by(CheckResultModel.checked_at)
        )
        if since is not None:
            statement = statement.where(CheckResultModel.checked_at >= since)
        models = self.session.execute(statement).scalars().all()
        return [self._to_domain(model) for model in models]

    def get_latest(self, monitor_id: int) -> CheckResult | None:
        statement = (
            select(CheckResultModel)
            .where(CheckResultModel.monitor_id == monitor_id)
            .order_by(CheckResultModel.checked_at.desc())
            .limit(1)
        )
        model = self.session.scalar(statement)
        if model is None:
            return None
        return self._to_domain(model)

    @staticmethod
    def _to_domain(model: CheckResultModel) -> CheckResult:
        return CheckResult(
            monitor_id=model.monitor_id,
            checked_at=model.checked_at,
            is_up=model.is_up,
            response_time_ms=model.response_time_ms,
        )
