from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
