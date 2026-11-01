from fastapi import APIRouter, Depends, HTTPException

from server.auth_dependencies import get_current_user
from server.database import session_scope
from server.models import User, UserSettings
from server.schemas.auth_schema import SettingsResponse, SettingsUpdateRequest


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/me", response_model=SettingsResponse)
def get_settings(user: User = Depends(get_current_user)):
    with session_scope() as session:
        settings = session.get(UserSettings, user.id)
        if settings is None:
            raise HTTPException(status_code=404, detail="Settings not found")
        return SettingsResponse(theme=settings.theme, preferences=settings.preferences)


@router.patch("/me", response_model=SettingsResponse)
def update_settings(data: SettingsUpdateRequest, user: User = Depends(get_current_user)):
    updates = data.model_dump(exclude_unset=True, exclude_none=True)
    with session_scope() as session:
        settings = session.get(UserSettings, user.id)
        if settings is None:
            settings = UserSettings(user_id=user.id)
            session.add(settings)
        for field, value in updates.items():
            setattr(settings, field, value)
        session.flush()
        return SettingsResponse(theme=settings.theme, preferences=settings.preferences)
