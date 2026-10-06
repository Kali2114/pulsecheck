from datetime import timedelta

from apscheduler.triggers.interval import IntervalTrigger

from app.domain.pinger import PingResult
from app.infrastructure.check_result_repository import SQLAlchemyCheckResultRepository
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from app.infrastructure.scheduler import create_scheduler
from tests.domain.utils import create_monitor
from tests.helpers.fake_pinger import FakePinger


class TestCreateScheduler:
    def _make_pinger(self) -> FakePinger:
        return FakePinger(PingResult(status_code=200, response_time_ms=100))

    def test_registers_one_non_overlapping_interval_job(self, session_factory):
        scheduler = create_scheduler(
            session_factory=session_factory,
            pinger=self._make_pinger(),
            interval_seconds=30,
        )

        jobs = scheduler.get_jobs()

        assert len(jobs) == 1
        job = jobs[0]
        assert isinstance(job.trigger, IntervalTrigger)
        assert job.trigger.interval == timedelta(seconds=30)
        assert job.max_instances == 1
        assert job.coalesce is True

    def test_job_runs_a_check_for_due_monitors(self, session_factory):
        with session_factory() as session:
            monitor = create_monitor()
            SQLAlchemyMonitorRepository(session).add_monitor(monitor)
            session.commit()

        scheduler = create_scheduler(
            session_factory=session_factory,
            pinger=self._make_pinger(),
        )

        scheduler.get_jobs()[0].func()

        with session_factory() as session:
            results = SQLAlchemyCheckResultRepository(session).list_for_monitor(
                monitor.id
            )
            saved_monitor = SQLAlchemyMonitorRepository(session).get_monitor(monitor.id)

            assert len(results) == 1
            assert results[0].is_up
            assert saved_monitor.last_checked_at == results[0].checked_at
