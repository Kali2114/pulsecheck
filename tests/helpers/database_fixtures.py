from datetime import timedelta

import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.config import settings
from app.infrastructure.check_result_repository import SQLAlchemyCheckResultRepository
from app.infrastructure.monitor_repository import SQLAlchemyMonitorRepository
from app.infrastructure.user_repository import SQLAlchemyUserRepository
from tests.domain.utils import create_monitor, create_user


@pytest.fixture(scope="session")
def migrated_database():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.attributes["database_url"] = settings.test_database_url

    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(settings.test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(engine, migrated_database):
    connection = engine.connect()
    transaction = connection.begin()

    yield sessionmaker(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    transaction.rollback()
    connection.close()


@pytest.fixture
def db_session(session_factory):
    session = session_factory()

    yield session

    session.close()


@pytest.fixture
def make_user(session_factory):
    created = 0

    def _make_user() -> int:
        nonlocal created
        created += 1
        with session_factory() as session:
            user = SQLAlchemyUserRepository(session).add_user(
                create_user(email=f"user{created}@example.com")
            )
            session.commit()
        return user.id

    return _make_user


@pytest.fixture
def add_monitor(session_factory):

    def _add_monitor(user_id, url="https://example.com"):
        with session_factory() as session:
            saved = SQLAlchemyMonitorRepository(session).add_monitor(
                create_monitor(
                    user_id=user_id, url=url, check_interval=timedelta(seconds=10)
                )
            )
            session.commit()
        return saved

    return _add_monitor


@pytest.fixture
def add_check_results(session_factory):

    def _add_check_results(*check_results):
        with session_factory() as session:
            repository = SQLAlchemyCheckResultRepository(session)
            for check_result in check_results:
                repository.add_check_result(check_result)
            session.commit()

    return _add_check_results
