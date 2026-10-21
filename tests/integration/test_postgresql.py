import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


POSTGRES_URL = os.getenv("FACTORYOPS_TEST_POSTGRES_URL")


@pytest.mark.skipif(
    not POSTGRES_URL,
    reason="FACTORYOPS_TEST_POSTGRES_URL is not configured for a dedicated test database",
)
def test_postgresql_migration_and_connectivity():
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", POSTGRES_URL.replace("%", "%%"))
    command.upgrade(config, "head")
    engine = create_engine(POSTGRES_URL)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT 1")) == 1
    assert "fo_batches" in inspect(engine).get_table_names()
