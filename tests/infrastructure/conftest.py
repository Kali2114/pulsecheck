import pytest
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.config import settings


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
