import shutil

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from server.auth_dependencies import get_current_user
from server.config import PRIVATE_STORAGE_DIR
from server.database import session_scope
from server.models import RefreshSession, User
from server.routers.auth import _clear_session_cookies
from server.schemas.auth_schema import (
    AccountDeleteRequest,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    UserResponse,
)
from server.security import hash_password, utc_now, verify_password


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
def update_profile(data: ProfileUpdateRequest, user: User = Depends(get_current_user)):
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    if not updates:
        return user
    with session_scope() as session:
        current = session.get(User, user.id)
        if current is None:
            raise HTTPException(status_code=404, detail="Account not found")
        for field, value in updates.items():
            setattr(current, field, value)
        try:
            session.flush()
        except IntegrityError as error:
            raise HTTPException(status_code=409, detail="Username or email is already in use") from error
        session.refresh(current)
        return UserResponse.model_validate(current)


@router.patch("/me/password")
def change_password(
    data: PasswordChangeRequest,
    response: Response,
    user: User = Depends(get_current_user),
):
    if data.current_password == data.new_password:
        raise HTTPException(status_code=422, detail="New password must be different")
    with session_scope() as session:
        current = session.get(User, user.id)
        if current is None or not verify_password(data.current_password, current.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        current.password_hash = hash_password(data.new_password)
        session.execute(
            update(RefreshSession)
            .where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=utc_now())
        )
    _clear_session_cookies(response)
    return {"status": "password updated; sign in again"}


@router.delete("/me", status_code=204)
def delete_account(
    data: AccountDeleteRequest,
    response: Response,
    user: User = Depends(get_current_user),
):
    with session_scope() as session:
        current = session.get(User, user.id)
        if current is None or not verify_password(data.password, current.password_hash):
            raise HTTPException(status_code=400, detail="Password is incorrect")
        session.delete(current)
    for directory in (
        PRIVATE_STORAGE_DIR / "generated" / str(user.id),
        PRIVATE_STORAGE_DIR / "avatars" / str(user.id),
    ):
        if directory.exists():
            shutil.rmtree(directory)
    _clear_session_cookies(response)
    return None
