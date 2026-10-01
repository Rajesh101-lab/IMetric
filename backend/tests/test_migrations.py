from pathlib import Path

from alembic import command
from alembic.config import Config
from uuid import uuid4

from sqlalchemy import MetaData, create_engine, inspect, insert, text

from app.db.migrations import upgrade_database
from app.db.models import Base


def _legacy_schema(connection):
    metadata = MetaData()
    for table in Base.metadata.sorted_tables:
        if table.name not in {"registration_requests", "refresh_jobs", "refresh_job_items"}:
            table.to_metadata(metadata)
    metadata.create_all(connection)
    user_id = uuid4()
    page_id = uuid4()
    connection.execute(insert(metadata.tables["users"]).values(
        id=user_id,
        username="legacy_owner",
        password_hash="existing-hash",
        is_active=True,
    ))
    connection.execute(insert(metadata.tables["pages"]).values(
        id=page_id,
        user_id=user_id,
        username="legacy",
    ))


def _assert_current_schema(connection):
    current = inspect(connection)
    assert set(Base.metadata.tables).issubset(set(current.get_table_names()))
    for table in Base.metadata.sorted_tables:
        expected = {column.name for column in table.columns}
        actual = {column["name"] for column in current.get_columns(table.name)}
        assert expected.issubset(actual), f"{table.name} is missing columns: {expected - actual}"


def _alembic_config(connection):
    config_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    config = Config(str(config_path))
    config.attributes["connection"] = connection
    return config


def test_upgrade_fresh_sqlite_database():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        upgrade_database(connection)
        _assert_current_schema(connection)
        assert "ck_pages_source" in {check["name"] for check in inspect(connection).get_check_constraints("pages")}
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "003_durable_refresh_jobs"
    engine.dispose()


def test_upgrade_unversioned_legacy_database_preserves_pages():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        _legacy_schema(connection)
        upgrade_database(connection)
        _assert_current_schema(connection)
        assert connection.execute(text("SELECT username FROM pages WHERE username = 'legacy'")).scalar_one() == "legacy"
        assert connection.execute(text("SELECT status FROM pages WHERE username = 'legacy'")).scalar_one() == "ready"
    engine.dispose()


def test_upgrade_from_initial_alembic_revision_preserves_pages():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        command.upgrade(_alembic_config(connection), "001_initial_schema")
        connection.execute(text(
            "INSERT INTO users (id, username, password_hash, created_at) "
            "VALUES ('00000000000000000000000000000001', 'agency', 'hashed', CURRENT_TIMESTAMP)"
        ))
        connection.execute(text(
            "INSERT INTO pages (id, user_id, username, created_at, updated_at) "
            "VALUES ('00000000000000000000000000000002', '00000000000000000000000000000001', 'legacy', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
        ))

        upgrade_database(connection)

        _assert_current_schema(connection)
        assert connection.execute(text("SELECT username FROM pages WHERE id = '00000000000000000000000000000002'")).scalar_one() == "legacy"
        assert connection.execute(text("SELECT status FROM pages WHERE username = 'legacy'")).scalar_one() == "ready"
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "003_durable_refresh_jobs"
    engine.dispose()


def test_refuses_to_stamp_incomplete_unversioned_database():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id CHAR(32) PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE sessions (id CHAR(32) PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE pages (id CHAR(32) PRIMARY KEY)"))
        connection.execute(text("CREATE TABLE page_snapshots (id CHAR(32) PRIMARY KEY)"))

        try:
            upgrade_database(connection)
        except RuntimeError as error:
            assert "missing columns" in str(error)
        else:
            raise AssertionError("An incomplete schema must not be stamped as a known baseline.")
    engine.dispose()