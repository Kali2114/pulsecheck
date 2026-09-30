from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, sessionmaker

from app.config import settings


class Base(MappedAsDataclass, DeclarativeBase):
    # MappedAsDataclass generates a real, typed __init__ for each model, so IDEs
    # and type checkers know which arguments a model accepts.
    pass


engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)
