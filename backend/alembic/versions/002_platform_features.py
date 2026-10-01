"""Add page metadata, campaigns, and registration requests.

Revision ID: 002_platform_features
Revises: 001_initial_schema
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_platform_features"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _indexes(table_name: str) -> set[str]:
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    tables = _tables()

    page_columns = _columns("pages")
    page_additions = (
        ("status", sa.String(length=20), "ready"),
        ("source", sa.String(length=20), "official"),
        ("fallback_reason", sa.String(length=50), None),
        ("error_kind", sa.String(length=50), None),
        ("error_message", sa.String(length=255), None),
    )
    for name, column_type, default in page_additions:
        if name not in page_columns:
            op.add_column(
                "pages",
                sa.Column(name, column_type, nullable=default is None, server_default=default),
            )
    page_checks = {check["name"] for check in sa.inspect(op.get_bind()).get_check_constraints("pages")}
    if "ck_pages_source" not in page_checks:
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("pages") as batch_op:
                batch_op.create_check_constraint("ck_pages_source", "source IN ('official', 'backup')")
        else:
            op.create_check_constraint("ck_pages_source", "pages", "source IN ('official', 'backup')")

    snapshot_columns = _columns("page_snapshots")
    if "source" not in snapshot_columns:
        op.add_column("page_snapshots", sa.Column("source", sa.String(length=20), nullable=False, server_default="official"))
    if "fallback_reason" not in snapshot_columns:
        op.add_column("page_snapshots", sa.Column("fallback_reason", sa.String(length=50), nullable=True))

    uuid_type = sa.Uuid(as_uuid=True)
    if "page_tags" not in tables:
        op.create_table(
            "page_tags",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("page_id", uuid_type, nullable=False),
            sa.Column("label", sa.String(length=32), nullable=False),
            sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("page_id", "label", name="uq_page_tags_page_label"),
        )
    if "ix_page_tags_page_id" not in _indexes("page_tags"):
        op.create_index("ix_page_tags_page_id", "page_tags", ["page_id"], unique=False)

    if "campaigns" not in tables:
        op.create_table(
            "campaigns",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("user_id", uuid_type, nullable=False),
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("description", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_campaigns_user_id" not in _indexes("campaigns"):
        op.create_index("ix_campaigns_user_id", "campaigns", ["user_id"], unique=False)

    if "campaign_pages" not in tables:
        op.create_table(
            "campaign_pages",
            sa.Column("campaign_id", uuid_type, nullable=False),
            sa.Column("page_id", uuid_type, nullable=False),
            sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["page_id"], ["pages.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("campaign_id", "page_id"),
        )

    if "registration_requests" not in tables:
        op.create_table(
            "registration_requests",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("username", sa.String(length=30), nullable=False),
            sa.Column("contact_email", sa.String(length=254), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("reviewed_by", uuid_type, nullable=True),
            sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="ck_registration_request_status"),
            sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
    if "ix_registration_requests_username" not in _indexes("registration_requests"):
        op.create_index("ix_registration_requests_username", "registration_requests", ["username"], unique=True)

    if "provider_usage" not in tables:
        op.create_table(
            "provider_usage",
            sa.Column("id", uuid_type, nullable=False),
            sa.Column("day_date", sa.String(length=10), nullable=False),
            sa.Column("provider_name", sa.String(length=30), nullable=False),
            sa.Column("agency_id", uuid_type, nullable=False),
            sa.Column("calls", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failures", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["agency_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("day_date", "provider_name", "agency_id", name="uq_provider_usage_day_provider_agency"),
        )
    if "ix_provider_usage_day_date" not in _indexes("provider_usage"):
        op.create_index("ix_provider_usage_day_date", "provider_usage", ["day_date"], unique=False)
    if "ix_provider_usage_agency_id" not in _indexes("provider_usage"):
        op.create_index("ix_provider_usage_agency_id", "provider_usage", ["agency_id"], unique=False)


def downgrade() -> None:
    tables = _tables()
    if "provider_usage" in tables:
        indexes = _indexes("provider_usage")
        for index_name in ("ix_provider_usage_agency_id", "ix_provider_usage_day_date"):
            if index_name in indexes:
                op.drop_index(index_name, table_name="provider_usage")
        op.drop_table("provider_usage")
    if "registration_requests" in tables:
        if "ix_registration_requests_username" in _indexes("registration_requests"):
            op.drop_index("ix_registration_requests_username", table_name="registration_requests")
        op.drop_table("registration_requests")
    if "campaign_pages" in tables:
        op.drop_table("campaign_pages")
    if "campaigns" in tables:
        if "ix_campaigns_user_id" in _indexes("campaigns"):
            op.drop_index("ix_campaigns_user_id", table_name="campaigns")
        op.drop_table("campaigns")
    if "page_tags" in tables:
        if "ix_page_tags_page_id" in _indexes("page_tags"):
            op.drop_index("ix_page_tags_page_id", table_name="page_tags")
        op.drop_table("page_tags")

    page_columns = _columns("pages")
    for name in ("error_message", "error_kind", "fallback_reason", "source", "status"):
        if name in page_columns:
            op.drop_column("pages", name)

    snapshot_columns = _columns("page_snapshots")
    for name in ("fallback_reason", "source"):
        if name in snapshot_columns:
            op.drop_column("page_snapshots", name)