from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_from_empty_database(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'migration.db').as_posix()}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    tables = set(inspect(create_engine(database_url)).get_table_names())
    assert "fo_suppliers" in tables
    assert "fo_quality_issue_batches" in tables
    assert "alembic_version" in tables
    command.downgrade(config, "base")
    remaining = set(inspect(create_engine(database_url)).get_table_names())
    assert not {name for name in remaining if name.startswith("fo_")}
    command.upgrade(config, "head")
