"""Persist refresh jobs and resumable page work.

Revision ID: 003_durable_refresh_jobs
Revises: 002_platform_features
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "003_durable_refresh_jobs"
down_revision: Union[str, None] = "002_platform_features"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    uuid_type = sa.Uuid(as_uuid=True)
    snapshot_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("page_snapshots")}
    if "ix_page_snapshots_fetched_at" not in snapshot_indexes:
        op.create_index("ix_page_snapshots_fetched_at", "page_snapshots", ["fetched_at"], unique=False)
    op.create_table(
        "refresh_jobs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("is_refresh_all", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("done", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('queued', 'running', 'completed', 'failed')", name="ck_refresh_jobs_status"),
        sa.CheckConstraint("total >= 0 AND done >= 0 AND failed >= 0", name="ck_refresh_jobs_counts_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_jobs_user_id", "refresh_jobs", ["user_id"], unique=False)
    op.create_index(
        "uq_refresh_jobs_active_user",
        "refresh_jobs",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('queued', 'running')"),
        sqlite_where=sa.text("status IN ('queued', 'running')"),
    )

    op.create_table(
        "refresh_job_items",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("job_id", uuid_type, nullable=False),
        sa.Column("page_id", uuid_type, nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
        sa.Column("lease_token", uuid_type, nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('queued', 'running', 'completed', 'failed')", name="ck_refresh_job_items_status"),
        sa.ForeignKeyConstraint(["job_id"], ["refresh_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_job_items_job_id", "refresh_job_items", ["job_id"], unique=False)
    op.create_index("ix_refresh_job_items_status_created", "refresh_job_items", ["status", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_refresh_job_items_status_created", table_name="refresh_job_items")
    op.drop_index("ix_refresh_job_items_job_id", table_name="refresh_job_items")
    op.drop_table("refresh_job_items")
    op.drop_index("uq_refresh_jobs_active_user", table_name="refresh_jobs")
    op.drop_index("ix_refresh_jobs_user_id", table_name="refresh_jobs")
    op.drop_table("refresh_jobs")
    snapshot_indexes = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("page_snapshots")}
    if "ix_page_snapshots_fetched_at" in snapshot_indexes:
        op.drop_index("ix_page_snapshots_fetched_at", table_name="page_snapshots")