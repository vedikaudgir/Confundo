import os
from pathlib import Path


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mockchat.db")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))
_COOKIE_SECURE_ENV = os.getenv("COOKIE_SECURE")
COOKIE_SECURE = (
    _COOKIE_SECURE_ENV.strip().lower() in {"1", "true", "yes"}
    if _COOKIE_SECURE_ENV is not None
    else APP_ENV in {"production", "prod"}
)
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", "").strip() or None
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").strip().lower()
if COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise ValueError("COOKIE_SAMESITE must be lax, strict, or none")
if APP_ENV in {"production", "prod"} and not COOKIE_SECURE:
    raise ValueError("COOKIE_SECURE cannot be disabled in production")
if COOKIE_SAMESITE == "none" and not COOKIE_SECURE:
    raise ValueError("COOKIE_SECURE must be true when COOKIE_SAMESITE is none")

ACCESS_COOKIE = "chattiebaby_access"
REFRESH_COOKIE = "chattiebaby_refresh"
CSRF_COOKIE = "chattiebaby_csrf"
MAX_AVATAR_BYTES = 5 * 1024 * 1024
MAX_AVATAR_PIXELS = 4_000_000
PRIVATE_STORAGE_DIR = Path(
    os.getenv("PRIVATE_STORAGE_DIR", str(Path(__file__).resolve().parent / "private"))
).resolve()
