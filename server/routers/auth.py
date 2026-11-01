from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError

from server.auth_dependencies import get_current_user
from server.config import (
    ACCESS_COOKIE,
    ACCESS_TOKEN_MINUTES,
    CSRF_COOKIE,
    COOKIE_DOMAIN,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    REFRESH_COOKIE,
)
from server.database import session_scope
from server.models import RefreshSession, User, UserSettings
from server.schemas.auth_schema import LoginRequest, RegisterRequest, UserResponse
from server.security import (
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    is_expired,
    utc_now,
    verify_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookies(response: Response, user_id: int, refresh_token: str, expires_at):
    access_token = create_access_token(user_id)
    access_max_age = ACCESS_TOKEN_MINUTES * 60
    refresh_max_age = max(1, int((expires_at - utc_now()).total_seconds()))
    cookie_options = {
        "secure": COOKIE_SECURE,
        "samesite": COOKIE_SAMESITE,
        "path": "/",
    }
    if COOKIE_DOMAIN:
        cookie_options["domain"] = COOKIE_DOMAIN
    response.set_cookie(
        ACCESS_COOKIE, access_token, httponly=True, max_age=access_max_age, **cookie_options
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh_token, httponly=True, max_age=refresh_max_age, **cookie_options
    )
    response.set_cookie(
        CSRF_COOKIE, create_csrf_token(), httponly=False, max_age=refresh_max_age, **cookie_options
    )


def _clear_session_cookies(response: Response):
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(
            name,
            path="/",
            secure=COOKIE_SECURE,
            httponly=name != CSRF_COOKIE,
            samesite=COOKIE_SAMESITE,
            domain=COOKIE_DOMAIN,
        )


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: RegisterRequest, response: Response):
    with session_scope() as session:
        user = User(
            username=data.username,
            email=data.email,
            password_hash=hash_password(data.password),
        )
        session.add(user)
        try:
            session.flush()
        except IntegrityError as error:
            raise HTTPException(status_code=409, detail="Username or email is already registered") from error
        session.add(UserSettings(user_id=user.id))
        token, token_hash, expires_at = create_refresh_token()
        session.add(
            RefreshSession(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        )
        session.flush()
        user_id = user.id
        user_response = UserResponse.model_validate(user)
    _set_session_cookies(response, user_id, token, expires_at)
    return user_response


@router.post("/login", response_model=UserResponse)
def login(data: LoginRequest, response: Response):
    identifier = data.identifier.lower()
    with session_scope() as session:
        user = session.scalar(
            select(User).where(
                or_(User.email == identifier, func.lower(User.username) == identifier)
            )
        )
        if user is None or not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid username/email or password")
        token, token_hash, expires_at = create_refresh_token()
        session.add(RefreshSession(user_id=user.id, token_hash=token_hash, expires_at=expires_at))
        session.flush()
        user_id = user.id
        user_response = UserResponse.model_validate(user)
    _set_session_cookies(response, user_id, token, expires_at)
    return user_response


@router.post("/refresh", response_model=UserResponse)
def refresh(request: Request, response: Response):
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if not raw_token:
        _clear_session_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh session is missing")

    token_hash = hash_refresh_token(raw_token)
    with session_scope() as session:
        current = session.scalar(
            select(RefreshSession).where(RefreshSession.token_hash == token_hash)
        )
        if current is None or current.revoked_at is not None or is_expired(current.expires_at):
            _clear_session_cookies(response)
            raise HTTPException(status_code=401, detail="Refresh session is invalid or expired")
        now = utc_now()
        result = session.execute(
            update(RefreshSession)
            .where(RefreshSession.id == current.id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        if result.rowcount != 1:
            _clear_session_cookies(response)
            raise HTTPException(status_code=401, detail="Refresh session has already been used")
        token, replacement_hash, expires_at = create_refresh_token()
        session.add(
            RefreshSession(
                user_id=current.user_id,
                token_hash=replacement_hash,
                expires_at=expires_at,
            )
        )
        user = session.scalar(select(User).where(User.id == current.user_id))
        if user is None:
            _clear_session_cookies(response)
            raise HTTPException(status_code=401, detail="Account no longer exists")
        user_id = user.id
        user_response = UserResponse.model_validate(user)
    _set_session_cookies(response, user_id, token, expires_at)
    return user_response


@router.post("/logout")
def logout(request: Request, response: Response):
    raw_token = request.cookies.get(REFRESH_COOKIE)
    if raw_token:
        with session_scope() as session:
            session.execute(
                update(RefreshSession)
                .where(
                    RefreshSession.token_hash == hash_refresh_token(raw_token),
                    RefreshSession.revoked_at.is_(None),
                )
                .values(revoked_at=utc_now())
            )
    _clear_session_cookies(response)
    return {"status": "logged out"}


@router.get("/me", response_model=UserResponse)
def auth_me(user: User = Depends(get_current_user)):
    return user
