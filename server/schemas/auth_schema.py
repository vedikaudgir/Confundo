import re
import json
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=32)]
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]
Email = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=254)]


def validate_email(value: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise ValueError("Enter a valid email address")
    return value


class RegisterRequest(BaseModel):
    username: Username
    email: Email
    password: Password

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return validate_email(value)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            raise ValueError("Username may contain letters, numbers, periods, underscores, and hyphens")
        return value.lower()


class LoginRequest(BaseModel):
    identifier: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=254)]
    password: Password


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    username: Username | None = None
    email: Email | None = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return validate_email(value) if value is not None else None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            raise ValueError("Username may contain letters, numbers, periods, underscores, and hyphens")
        return value.lower() if value is not None else None


class PasswordChangeRequest(BaseModel):
    current_password: Password
    new_password: Password


class AccountDeleteRequest(BaseModel):
    password: Password


class SettingsResponse(BaseModel):
    theme: str
    preferences: dict = Field(default_factory=dict)


class SettingsUpdateRequest(BaseModel):
    theme: str | None = None
    preferences: dict | None = None

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, value: str | None) -> str | None:
        if value is not None and value not in {"light", "dark"}:
            raise ValueError("Theme must be light or dark")
        return value

    @field_validator("preferences")
    @classmethod
    def validate_preferences(cls, value: dict | None) -> dict | None:
        if value is None:
            return None
        if len(value) > 50 or any(not isinstance(key, str) or len(key) > 64 for key in value):
            raise ValueError("Preferences must contain at most 50 short string keys")
        if len(json.dumps(value, separators=(",", ":"))) > 10_000:
            raise ValueError("Preferences must be 10 KB or smaller")
        return value
