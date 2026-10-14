from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.config import settings
from app.domain.exceptions import (
    EmailAlreadyRegistered,
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


@app.exception_handler(EmailAlreadyRegistered)
def email_already_registered_handler(
    request: Request, exc: EmailAlreadyRegistered
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)}
    )


@app.exception_handler(PasswordTooLong)
def password_too_long(request: Request, exc: PasswordTooLong) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)}
    )
