from datetime import datetime, timedelta

from sqlalchemy import DateTime
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
