"""Database engine/session construction with no legacy runtime imports."""

from collections.abc import Callable

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:CHANGE_ME@localhost:5432/postgres"


def create_database_engine(database_url: str, *, echo: bool = False) -> Engine:
    kwargs: dict = {"echo": echo, "pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **kwargs)


def create_session_factory(engine: Engine) -> Callable[[], Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
