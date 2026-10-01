from datetime import datetime, timedelta

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base


class MonitorModel(Base):
    __tablename__ = "monitors"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    user_id: Mapped[int] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    check_interval: Mapped[timedelta] = mapped_column(
        nullable=False,
    )

    timeout: Mapped[int] = mapped_column(
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(
        nullable=False,
    )


class CheckResultModel(Base):
    __tablename__ = "check_results"
    __table_args__ = (
        Index("ix_check_results_monitor_checked_at", "monitor_id", "checked_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    monitor_id: Mapped[int] = mapped_column(
        ForeignKey("monitors.id", ondelete="CASCADE")
    )
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_up: Mapped[bool] = mapped_column(nullable=False)
    response_time_ms: Mapped[int | None] = mapped_column()
