"""Console entrypoints for the isolated FactoryOps backend."""

import json
import os

import uvicorn

from factoryops.infrastructure.db.seed import seed_database
from factoryops.infrastructure.db.session import (
    DEFAULT_DATABASE_URL,
    create_database_engine,
    create_session_factory,
)


def run_api() -> None:
    uvicorn.run(
        "factoryops.bootstrap.app:app",
        host=os.getenv("FACTORYOPS_HOST", "127.0.0.1"),
        port=int(os.getenv("FACTORYOPS_PORT", "8001")),
        reload=False,
    )


def seed() -> None:
    database_url = os.getenv("FACTORYOPS_DATABASE_URL", DEFAULT_DATABASE_URL)
    engine = create_database_engine(database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        result = seed_database(session)
    print(json.dumps(result, indent=2, sort_keys=True))
