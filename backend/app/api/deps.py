from typing import Optional
from urllib.parse import urlsplit
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import verify_csrf_token
from app.db.session import get_db
from app.db.models import User
from app.services import auth as auth_service

COOKIE_NAME = "__Host-session_id" if settings.ENV == "production" else "session_id"


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency for protected routes.
    Reads session cookie, validates session hash, idle/absolute expiry, and is_active flag.
    Returns authenticated User model or raises 401.
    """
    raw_token = request.cookies.get(COOKIE_NAME)
    if not raw_token:
        # Fallback to standard cookie name if __Host- prefix was configured but dev environment set session_id
        raw_token = request.cookies.get("session_id")

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Session expired or missing. Please sign in."}
        )

    session_obj = await auth_service.get_session_by_token(db, raw_token)
    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Session expired or invalid. Please sign in again."}
        )

    is_valid = await auth_service.validate_session(db, session_obj)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Session expired. Please sign in again."}
        )

    # Fetch user model explicitly (async sessions can't lazy-load relationships)
    from sqlalchemy import select
    from app.db.models import User as UserModel
    user_stmt = select(UserModel).where(UserModel.id == session_obj.user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHENTICATED", "message": "Account deactivated or invalid."}
        )

    return user


def verify_csrf(request: Request) -> None:
    """
    Verifies double-submit CSRF token for state-changing requests.
    Validates X-CSRF-Token header matches csrf_token cookie and verifies Origin/Referer headers.
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return

    cookie_csrf = request.cookies.get("csrf_token")
    header_csrf = request.headers.get("X-CSRF-Token")

    if not verify_csrf_token(cookie_csrf, header_csrf):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "CSRF_FAILED", "message": "CSRF token missing or invalid."}
        )

    # Origin / Referer check
    origin = request.headers.get("origin") or request.headers.get("referer")
    if origin:
        try:
            origin_url = urlsplit(origin)
            origin_base = f"{origin_url.scheme}://{origin_url.netloc}".lower()
        except ValueError:
            origin_base = ""

        request_origin = f"{request.url.scheme}://{request.url.netloc}".lower()
        configured_origins = set()
        for allowed_origin in settings.CORS_ORIGINS:
            allowed_url = urlsplit(allowed_origin)
            if allowed_url.scheme and allowed_url.netloc:
                configured_origins.add(f"{allowed_url.scheme}://{allowed_url.netloc}".lower())

        if origin_base not in configured_origins and origin_base != request_origin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "CSRF_ORIGIN_FORBIDDEN", "message": "Untrusted request origin."}
            )


async def get_registration_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    configured_admin = settings.INITIAL_USER.strip().lower()
    if not configured_admin or current_user.username != configured_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "ADMIN_REQUIRED",
                "message": "Only the configured workspace owner can review registration requests.",
            },
        )
    return current_user
