from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.core.config import settings
from app.core.logging import logger
from app.core.security import (
    hash_password,
    verify_password,
    dummy_verify_password,
    generate_opaque_token,
    hash_token,
)
from app.db.models import User, Session


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def create_session(
    db: AsyncSession,
    user_id: UUID,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Tuple[Session, str]:
    raw_token = generate_opaque_token()
    token_h = hash_token(raw_token)
    now = utc_now()
    expires = now + timedelta(hours=settings.SESSION_ABSOLUTE_HOURS)

    session_obj = Session(
        user_id=user_id,
        token_hash=token_h,
        created_at=now,
        last_seen_at=now,
        expires_at=expires,
        ip=ip[:45] if ip else None,
        user_agent=user_agent[:512] if user_agent else None,
    )
    db.add(session_obj)
    await db.commit()
    await db.refresh(session_obj)
    return session_obj, raw_token


async def get_session_by_token(db: AsyncSession, raw_token: str) -> Optional[Session]:
    token_h = hash_token(raw_token)
    stmt = select(Session).where(Session.token_hash == token_h)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def validate_session(db: AsyncSession, session_obj: Session) -> bool:
    now = utc_now()
    expires_at = ensure_utc(session_obj.expires_at)
    last_seen_at = ensure_utc(session_obj.last_seen_at)

    if expires_at and expires_at <= now:
        await db.delete(session_obj)
        await db.commit()
        return False

    if last_seen_at:
        idle_limit = last_seen_at + timedelta(minutes=settings.SESSION_IDLE_MINUTES)
        if idle_limit <= now:
            await db.delete(session_obj)
            await db.commit()
            return False

    stmt = select(User.is_active).where(User.id == session_obj.user_id)
    res = await db.execute(stmt)
    is_active = res.scalar_one_or_none()
    if not is_active:
        await db.delete(session_obj)
        await db.commit()
        return False

    session_obj.last_seen_at = now
    await db.commit()
    return True


async def invalidate_session(db: AsyncSession, raw_token: str) -> None:
    token_h = hash_token(raw_token)
    stmt = delete(Session).where(Session.token_hash == token_h)
    await db.execute(stmt)
    await db.commit()


async def invalidate_all_user_sessions(db: AsyncSession, user_id: UUID) -> None:
    stmt = delete(Session).where(Session.user_id == user_id)
    await db.execute(stmt)
    await db.commit()


async def authenticate_user(
    db: AsyncSession,
    username: str,
    password: str,
    ip: Optional[str] = None
) -> Tuple[Optional[User], Optional[str]]:
    clean_username = username.strip().lower()
    now = utc_now()

    stmt = select(User).where(User.username == clean_username)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        dummy_verify_password()
        logger.info(f"Failed login attempt for unknown user '{clean_username}' from IP {ip}")
        return None, "Invalid Agency ID or password."

    locked_until = ensure_utc(user.locked_until)
    if locked_until and locked_until > now:
        logger.warning(f"Login attempt on locked account '{clean_username}' from IP {ip}")
        return None, "Invalid Agency ID or password."

    if not user.is_active:
        logger.warning(f"Login attempt on inactive account '{clean_username}' from IP {ip}")
        return None, "Invalid Agency ID or password."

    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= 5:
            user.locked_until = now + timedelta(minutes=15)
            logger.warning(f"Account '{clean_username}' locked for 15m after 5 failed attempts from IP {ip}")
        await db.commit()
        return None, "Invalid Agency ID or password."

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    await db.commit()
    logger.info(f"Successful login for user '{clean_username}' from IP {ip}")
    return user, None


async def seed_initial_user_if_empty(db: AsyncSession) -> None:
    if not settings.INITIAL_USER or not settings.INITIAL_PASSWORD:
        return

    stmt = select(User).limit(1)
    res = await db.execute(stmt)
    if res.scalar_one_or_none() is not None:
        return

    clean_uname = settings.INITIAL_USER.strip().lower()
    phash = hash_password(settings.INITIAL_PASSWORD)
    user = User(
        username=clean_uname,
        password_hash=phash,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    logger.warning(f"Seeded initial agency user '{clean_uname}' from env (CHANGE THIS PASSWORD!)")
