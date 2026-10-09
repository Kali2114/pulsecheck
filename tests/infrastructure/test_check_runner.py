from datetime import UTC, datetime

import pytest

from app.domain.pinger import PingResult
from app.infrastructure.check_result_repository import SQLAlchemyCheckResultRepository
from app.infrastructure.check_runner import run_check
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from tests.domain.utils import create_monitor
from tests.helpers.fake_pinger import FakePinger


class TestCheckRunner:

    def test_run_check_commits_result_and_updates_monitor(
        self, session_factory, make_user
    ):
        now = datetime(2026, 10, 5, 18, 0, tzinfo=UTC)
        pinger = FakePinger(
            PingResult(
                status_code=200,
                response_time_ms=100,
            )
        )
        with session_factory() as session:
            monitor_repository = SQLAlchemyMonitorRepository(session)

            monitor = create_monitor(user_id=make_user())
            monitor_repository.add_monitor(monitor)

            session.commit()

        run_check(
            session_factory=session_factory,
            pinger=pinger,
            now=now,
        )

        with session_factory() as session:
            monitor_repository = SQLAlchemyMonitorRepository(session)
            check_result_repository = SQLAlchemyCheckResultRepository(session)

            saved_monitor = monitor_repository.get_monitor(monitor.id)
            results = check_result_repository.list_for_monitor(monitor.id)

            assert saved_monitor.last_checked_at == now
            assert len(results) == 1
            assert results[0].monitor_id == monitor.id
            assert results[0].checked_at == now
            assert results[0].is_up

    def test_run_check_rolls_back_whole_run_when_a_ping_fails(
        self, session_factory, make_user
    ):
        now = datetime(2026, 10, 5, 18, 0, tzinfo=UTC)
        pinger = FakePinger(
            PingResult(
                status_code=200,
                response_time_ms=100,
            ),
            failing_urls={"http://bad.example.com"},
        )

        with session_factory() as session:
            monitor_repository = SQLAlchemyMonitorRepository(session)

            # Monitors are checked in id order, so the good one is written before
            # the bad one raises; that leaves something for the rollback to undo.
            user_id = make_user()
            good_monitor = create_monitor(
                user_id=user_id, url="http://good.example.com"
            )
            bad_monitor = create_monitor(user_id=user_id, url="http://bad.example.com")
            monitor_repository.add_monitor(good_monitor)
            monitor_repository.add_monitor(bad_monitor)
            session.commit()

        with pytest.raises(RuntimeError):
            run_check(
                session_factory=session_factory,
                pinger=pinger,
                now=now,
            )

        with session_factory() as session:
            monitor_repository = SQLAlchemyMonitorRepository(session)
            check_result_repository = SQLAlchemyCheckResultRepository(session)

            saved_good_monitor = monitor_repository.get_monitor(good_monitor.id)
            results = check_result_repository.list_for_monitor(good_monitor.id)

            assert results == []
            assert saved_good_monitor.last_checked_at is None
