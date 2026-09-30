import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    BigInteger,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    TypeDecorator,
    CHAR,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses PostgreSQL's native UUID type when available,
    otherwise stores as CHAR(32) in hex format (works with SQLite).
    """
    impl = CHAR(32)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
        if isinstance(value, uuid.UUID):
            return value.hex
        return uuid.UUID(value).hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    failed_login_count = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="user", cascade="all, delete-orphan")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

    user = relationship("User", back_populates="sessions")


class Page(Base):
    __tablename__ = "pages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    username = Column(String(30), nullable=False)
    status = Column(String(20), default="ready", nullable=False)  # "pending", "ready", "failed"
    source = Column(String(20), default="official", nullable=False)  # "official" or "backup"
    fallback_reason = Column(String(50), nullable=True)
    error_kind = Column(String(50), nullable=True)
    error_message = Column(String(255), nullable=True)
    followers = Column(BigInteger, default=0, nullable=False)
    last_reel_likes = Column(BigInteger, nullable=True)
    last_reel_views = Column(BigInteger, nullable=True)
    avg_views = Column(Float, default=0.0, nullable=False)
    median_views = Column(Float, default=0.0, nullable=False)
    avg_likes = Column(Float, default=0.0, nullable=False)
    like_to_view_ratio = Column(Float, default=0.0, nullable=False)
    avg_views_per_follower = Column(Float, default=0.0, nullable=False)
    reels_sampled = Column(Integer, default=0, nullable=False)
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)
    last_refresh_error = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="pages")
    snapshots = relationship("PageSnapshot", back_populates="page", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "username", name="uq_pages_user_username"),
        CheckConstraint("followers >= 0", name="ck_pages_followers_non_negative"),
        CheckConstraint("reels_sampled >= 0", name="ck_pages_reels_sampled_non_negative"),
        CheckConstraint("source IN ('official', 'backup')", name="ck_pages_source"),
    )


class PageSnapshot(Base):
    __tablename__ = "page_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    page_id = Column(GUID(), ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(20), default="official", nullable=False)
    fallback_reason = Column(String(50), nullable=True)
    followers = Column(BigInteger, default=0, nullable=False)
    last_reel_likes = Column(BigInteger, nullable=True)
    last_reel_views = Column(BigInteger, nullable=True)
    avg_views = Column(Float, default=0.0, nullable=False)
    median_views = Column(Float, default=0.0, nullable=False)
    avg_likes = Column(Float, default=0.0, nullable=False)
    like_to_view_ratio = Column(Float, default=0.0, nullable=False)
    avg_views_per_follower = Column(Float, default=0.0, nullable=False)
    reels_sampled = Column(Integer, default=0, nullable=False)
    fetched_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    page = relationship("Page", back_populates="snapshots")

    __table_args__ = (
        CheckConstraint("followers >= 0", name="ck_snapshots_followers_non_negative"),
        CheckConstraint("reels_sampled >= 0", name="ck_snapshots_reels_sampled_non_negative"),
    )


class ProviderUsage(Base):
    __tablename__ = "provider_usage"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    day_date = Column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    provider_name = Column(String(30), nullable=False)
    agency_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    calls = Column(Integer, default=0, nullable=False)
    failures = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("day_date", "provider_name", "agency_id", name="uq_provider_usage_day_provider_agency"),
    )
