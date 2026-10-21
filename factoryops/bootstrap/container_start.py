"""Migrate, seed, and start the self-contained FactoryOps container."""

import os

import uvicorn
from alembic import command
from alembic.config import Config

from factoryops.infrastructure.db.seed import seed_database
from factoryops.infrastructure.db.session import create_database_engine, create_session_factory


def prepare_database(database_url: str, *, load_seed: bool = True) -> None:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")
    if load_seed:
        engine = create_database_engine(database_url)
        with create_session_factory(engine)() as session:
            seed_database(session)
        engine.dispose()


def main() -> None:
    database_url = os.environ["FACTORYOPS_DATABASE_URL"]
    prepare_database(
        database_url,
        load_seed=os.getenv("FACTORYOPS_SEED_DATA", "true").lower() == "true",
    )
    uvicorn.run(
        "factoryops.bootstrap.app:app",
        host="0.0.0.0",
        port=int(os.getenv("FACTORYOPS_PORT", "8001")),
    )


if __name__ == "__main__":
    main()
