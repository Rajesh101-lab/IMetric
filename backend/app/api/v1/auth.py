from uuid import UUID
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_registration_admin, verify_csrf, COOKIE_NAME
from app.core.config import settings
from app.core.security import generate_csrf_token
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
    CSRFResponse,
    MessageResponse,
    RegistrationRequestResponse,
    RegistrationSubmissionResponse,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/csrf", response_model=CSRFResponse)
async def get_csrf_token(response: Response):
    """
    Returns pre-session CSRF token and sets double-submit csrf_token cookie.
    Publicly accessible endpoint.
    """
    token = generate_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # Accessible to frontend JS to mirror in X-CSRF-Token header
        samesite="lax",
        path="/",
        secure=(settings.ENV == "production"),
    )
    response.headers["Cache-Control"] = "no-store"
    return CSRFResponse(csrf_token=token)


@router.post("/login", response_model=UserResponse)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates agency user with Agency ID and password.
    Sets HttpOnly, SameSite=Lax session cookie.
    """
    verify_csrf(request)

    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    user, error = await auth_service.authenticate_user(db, req.username, req.password, ip)
    if error or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid Agency ID or password."}
        )

    # Issue opaque session token & store hash
    session_obj, raw_token = await auth_service.create_session(db, user.id, ip, user_agent)

    # Set secure session cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        path="/",
        secure=(settings.ENV == "production"),
        max_age=settings.SESSION_ABSOLUTE_HOURS * 3600,
    )
    response.headers["Cache-Control"] = "no-store"
    return UserResponse(
        id=user.id,
        username=user.username,
        is_admin=user.username == settings.INITIAL_USER.strip().lower(),
    )


@router.post("/register", response_model=RegistrationSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def register(
    req: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Submits a registration request for workspace-owner approval."""
    verify_csrf(request)
    registration_request = await auth_service.submit_registration_request(
        db, req.username, req.password, req.contact_email
    )
    response.headers["Cache-Control"] = "no-store"
    return RegistrationSubmissionResponse(username=registration_request.username, status="pending")


@router.get("/registration-requests", response_model=list[RegistrationRequestResponse])
async def list_registration_requests(
    admin: User = Depends(get_registration_admin),
    db: AsyncSession = Depends(get_db),
):
    requests = await auth_service.list_registration_requests(db)
    return [RegistrationRequestResponse.model_validate(item) for item in requests]


@router.post("/registration-requests/{request_id}/approve", response_model=RegistrationRequestResponse)
async def approve_registration_request(
    request_id: UUID,
    request: Request,
    admin: User = Depends(get_registration_admin),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf(request)
    item = await auth_service.review_registration_request(db, request_id, admin.id, approve=True)
    return RegistrationRequestResponse.model_validate(item)


@router.post("/registration-requests/{request_id}/reject", response_model=RegistrationRequestResponse)
async def reject_registration_request(
    request_id: UUID,
    request: Request,
    admin: User = Depends(get_registration_admin),
    db: AsyncSession = Depends(get_db),
):
    verify_csrf(request)
    item = await auth_service.review_registration_request(db, request_id, admin.id, approve=False)
    return RegistrationRequestResponse.model_validate(item)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Logs out the current agency user, invalidating the session."""
    verify_csrf(request)

    raw_token = request.cookies.get(COOKIE_NAME) or request.cookies.get("session_id")
    if raw_token:
        await auth_service.invalidate_session(db, raw_token)

    response.delete_cookie(key=COOKIE_NAME, path="/")
    response.delete_cookie(key="session_id", path="/")
    response.headers["Cache-Control"] = "no-store"
    return MessageResponse(message="Successfully logged out.")


@router.get("/me", response_model=UserResponse)
async def get_me(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Returns the currently authenticated agency user."""
    response.headers["Cache-Control"] = "no-store"
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_admin=current_user.username == settings.INITIAL_USER.strip().lower(),
    )
