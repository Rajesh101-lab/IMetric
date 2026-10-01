from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection


_BASELINE_TABLES = {"users", "sessions", "pages", "page_snapshots"}
_BASELINE_REQUIRED_COLUMNS = {
    "users": {"id", "username", "password_hash", "is_active", "failed_login_count", "locked_until", "created_at", "last_login_at"},
    "sessions": {"id", "user_id", "token_hash", "created_at", "last_seen_at", "expires_at", "ip", "user_agent"},
    "pages": {
        "id", "user_id", "username", "followers", "last_reel_likes", "last_reel_views", "avg_views",
        "median_views", "avg_likes", "like_to_view_ratio", "avg_views_per_follower", "reels_sampled",
        "last_refreshed_at", "last_refresh_error", "created_at", "updated_at",
    },
    "page_snapshots": {
        "id", "page_id", "followers", "last_reel_likes", "last_reel_views", "avg_views", "median_views",
        "avg_likes", "like_to_view_ratio", "avg_views_per_follower", "reels_sampled", "fetched_at",
    },
}
_MIGRATION_LOCK_ID = 0x494D4554524943


def upgrade_database(connection: Connection) -> None:
    """Upgrade the schema before serving requests, adopting legacy create_all databases."""
    if connection.dialect.name == "postgresql":
        connection.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": _MIGRATION_LOCK_ID})

    config_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    config = Config(str(config_path))
    config.attributes["connection"] = connection
    tables = set(inspect(connection).get_table_names())

    if "alembic_version" not in tables:
        existing_baseline = tables & _BASELINE_TABLES
        if existing_baseline and not _BASELINE_TABLES.issubset(tables):
            missing = ", ".join(sorted(_BASELINE_TABLES - tables))
            raise RuntimeError(f"Cannot safely adopt this unversioned database; missing baseline tables: {missing}.")
        if _BASELINE_TABLES.issubset(tables):
            inspector = inspect(connection)
            for table_name, required_columns in _BASELINE_REQUIRED_COLUMNS.items():
                actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
                missing_columns = required_columns - actual_columns
                if missing_columns:
                    missing = ", ".join(sorted(missing_columns))
                    raise RuntimeError(
                        f"Cannot safely adopt this unversioned database; {table_name} is missing columns: {missing}."
                    )
            command.stamp(config, "001_initial_schema")

    command.upgrade(config, "head")