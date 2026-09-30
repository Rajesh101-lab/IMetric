"""Initial Schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('failed_login_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)

    # sessions table
    op.create_table(
        'sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(512), nullable=True),
    )
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('ix_sessions_token_hash', 'sessions', ['token_hash'], unique=True)

    # pages table
    op.create_table(
        'pages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('username', sa.String(30), nullable=False),
        sa.Column('followers', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('last_reel_likes', sa.BigInteger(), nullable=True),
        sa.Column('last_reel_views', sa.BigInteger(), nullable=True),
        sa.Column('avg_views', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('median_views', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('avg_likes', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('like_to_view_ratio', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('avg_views_per_follower', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('reels_sampled', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_refreshed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_refresh_error', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('user_id', 'username', name='uq_pages_user_username'),
        sa.CheckConstraint('followers >= 0', name='ck_pages_followers_non_negative'),
        sa.CheckConstraint('reels_sampled >= 0', name='ck_pages_reels_sampled_non_negative'),
    )
    op.create_index('ix_pages_user_id', 'pages', ['user_id'])

    # page_snapshots table
    op.create_table(
        'page_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('page_id', UUID(as_uuid=True), sa.ForeignKey('pages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('followers', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('last_reel_likes', sa.BigInteger(), nullable=True),
        sa.Column('last_reel_views', sa.BigInteger(), nullable=True),
        sa.Column('avg_views', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('median_views', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('avg_likes', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('like_to_view_ratio', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('avg_views_per_follower', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('reels_sampled', sa.Integer(), server_default='0', nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('followers >= 0', name='ck_snapshots_followers_non_negative'),
        sa.CheckConstraint('reels_sampled >= 0', name='ck_snapshots_reels_sampled_non_negative'),
    )
    op.create_index('ix_page_snapshots_page_id', 'page_snapshots', ['page_id'])


def downgrade() -> None:
    op.drop_table('page_snapshots')
    op.drop_table('pages')
    op.drop_table('sessions')
    op.drop_table('users')
