from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

MIN_SECRET_KEY_BYTES = 32


class Settings(BaseSettings):
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_test_db: str
    postgres_port: int
    postgres_host: str = "localhost"
    scheduler_enabled: bool = True
    secret_key: str
    token_lifetime_hours: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("secret_key")
    @classmethod
    def secret_key_must_be_long_enough(cls, value: str) -> str:
        if len(value.encode("utf-8")) < MIN_SECRET_KEY_BYTES:
            raise ValueError(f"must be at least {MIN_SECRET_KEY_BYTES} bytes for HS256")
        return value

    @field_validator("token_lifetime_hours")
    @classmethod
    def token_lifetime_must_be_positive(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("token_lifetime_hours must be positive")
        return value

    def _build_database_url(self, database_name: str) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=database_name,
        )

    @property
    def database_url(self) -> URL:
        return self._build_database_url(self.postgres_db)

    @property
    def test_database_url(self) -> URL:
        return self._build_database_url(self.postgres_test_db)


settings = Settings()
