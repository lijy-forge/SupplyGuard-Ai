from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from factoryops.bootstrap.app import create_app
from factoryops.infrastructure.db.base import Base
from factoryops.infrastructure.db.seed import seed_database
from factoryops.infrastructure.db.session import create_database_engine, create_session_factory
from factoryops.infrastructure.db.uow import SqlAlchemyUnitOfWork


@pytest.fixture()
def database_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'factoryops-test.db').as_posix()}"


@pytest.fixture()
def session_factory(database_url):
    engine = create_database_engine(database_url)
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        seed_database(session)
    yield factory
    engine.dispose()


@pytest.fixture()
def uow_factory(session_factory):
    return lambda: SqlAlchemyUnitOfWork(session_factory)


@pytest.fixture()
def client(database_url) -> Iterator[TestClient]:
    app = create_app(database_url, initialize_schema=True)
    with create_session_factory(app.state.engine)() as session:
        seed_database(session)
    with TestClient(app) as test_client:
        yield test_client
    app.state.engine.dispose()
