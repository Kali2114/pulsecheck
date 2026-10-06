from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
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
