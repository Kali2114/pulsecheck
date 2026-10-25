from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.monitors import monitors_router
from app.config import settings
from app.domain.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidToken,
    MonitorNotFound,
    PasswordTooLong,
)
from app.infrastructure.scheduler_runner import (
    start_scheduler,
    stop_scheduler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    client = None

    if settings.scheduler_enabled:
        scheduler, client = start_scheduler()

    try:
        yield
    finally:
        if scheduler is not None and client is not None:
            stop_scheduler(scheduler, client)


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(monitors_router)


@app.exception_handler(EmailAlreadyRegistered)
def email_already_registered_handler(
    _request: Request, exc: EmailAlreadyRegistered
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
    )


@app.exception_handler(PasswordTooLong)
def password_too_long(_request: Request, exc: PasswordTooLong) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)}
    )


@app.exception_handler(InvalidCredentials)
def invalid_credentials_handler(
    _request: Request,
    exc: InvalidCredentials,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(InvalidToken)
def invalid_token_handler(
    _request: Request,
    exc: InvalidToken,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(MonitorNotFound)
def monitor_not_found_handler(
    _request: Request,
    exc: MonitorNotFound,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )
