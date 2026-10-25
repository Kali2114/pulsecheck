from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class MonitorCreate(BaseModel):
    url: str
    check_interval_seconds: int = Field(ge=10, le=86400)
    timeout_seconds: int = Field(ge=1, le=60)
    retry_count: int = Field(ge=1)


class MonitorRead(BaseModel):

    id: int
    url: str
    check_interval_seconds: int
    timeout_seconds: int
    retry_count: int
    last_checked_at: datetime | None


class MonitorUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str | None = None
    check_interval_seconds: int | None = Field(default=None, ge=10, le=86400)
    timeout_seconds: int | None = Field(default=None, ge=1, le=60)
    retry_count: int | None = Field(default=None, ge=1)

    @field_validator(
        "url",
        "check_interval_seconds",
        "timeout_seconds",
        "retry_count",
    )
    @classmethod
    def fields_cannot_be_null(cls, value):
        if value is None:
            raise ValueError("field cannot be null")
        return value
