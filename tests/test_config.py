import pytest
from pydantic import ValidationError

from app.config import MIN_SECRET_KEY_BYTES, Settings


def create_settings(**kwargs) -> Settings:
    payload = {
        "postgres_user": "pulse_user",
        "postgres_password": "secret",
        "postgres_db": "pulsecheck",
        "postgres_test_db": "pulsecheck_test",
        "postgres_port": 5434,
        "secret_key": "a" * 32,
    }
    payload.update(kwargs)
    return Settings(_env_file=None, **payload)


@pytest.fixture(autouse=True)
def clear_postgres_env(monkeypatch):
    for name in (
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_TEST_DB",
        "POSTGRES_PORT",
        "POSTGRES_HOST",
    ):
        monkeypatch.delenv(name, raising=False)


def test_database_url_is_built_from_settings():
    url = create_settings().database_url

    assert url.drivername == "postgresql+psycopg"
    assert url.username == "pulse_user"
    assert url.password == "secret"
    assert url.host == "localhost"
    assert url.port == 5434
    assert url.database == "pulsecheck"


def test_test_database_url_uses_test_database():
    url = create_settings().test_database_url

    assert url.database == "pulsecheck_test"


def test_host_can_be_overridden():
    url = create_settings(postgres_host="db").database_url

    assert url.host == "db"


def test_password_with_special_characters_survives_rendering():
    url = create_settings(postgres_password="p@ss:w/rd#1").database_url

    rendered = url.render_as_string(hide_password=False)

    assert "p%40ss%3Aw%2Frd%231" in rendered
    assert rendered.endswith("@localhost:5434/pulsecheck")


def test_str_of_url_hides_password():
    url = create_settings().database_url

    assert "secret" not in str(url)


def test_missing_required_setting_raises():
    with pytest.raises(ValueError):
        Settings(_env_file=None)


def test_secret_key_of_minimum_length_is_accepted():
    settings = create_settings(secret_key="a" * MIN_SECRET_KEY_BYTES)

    assert settings.secret_key == "a" * MIN_SECRET_KEY_BYTES


def test_secret_key_shorter_than_minimum_is_rejected():
    with pytest.raises(ValidationError, match="secret_key"):
        create_settings(secret_key="a" * (MIN_SECRET_KEY_BYTES - 1))


def test_secret_key_length_counts_bytes_not_characters():
    settings = create_settings(secret_key="ą" * 16)

    assert settings.secret_key == "ą" * 16
