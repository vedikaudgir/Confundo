import os
import secrets
import time
from pathlib import Path


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
IS_PRODUCTION = APP_ENV in {"production", "prod"}
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:////var/data/mockchat.db" if IS_PRODUCTION else "sqlite:///./mockchat.db",
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
JWT_SECRET_FILE = Path(
    os.getenv("JWT_SECRET_FILE", str(PROJECT_ROOT / ".secrets" / "jwt_secret"))
).expanduser()
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "30"))


def _validate_jwt_secret(secret: str) -> str:
    if len(secret.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 bytes")
    return secret


def _read_persisted_jwt_secret() -> str:
    try:
        secret = JWT_SECRET_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        secret = ""
    return _validate_jwt_secret(secret)


def _load_development_jwt_secret() -> str:
    JWT_SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    generated_secret = secrets.token_urlsafe(48)
    try:
        file_descriptor = os.open(
            JWT_SECRET_FILE,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        for attempt in range(10):
            try:
                return _read_persisted_jwt_secret()
            except RuntimeError:
                if attempt == 9:
                    raise
                time.sleep(0.01)

    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as secret_file:
            secret_file.write(generated_secret)
        try:
            os.chmod(JWT_SECRET_FILE, 0o600)
        except OSError:
            pass
        return _validate_jwt_secret(generated_secret)
    except OSError:
        try:
            os.close(file_descriptor)
        except OSError:
            pass
        raise


def _load_jwt_secret() -> str:
    configured_secret = os.getenv("JWT_SECRET_KEY")
    if configured_secret is not None:
        return _validate_jwt_secret(configured_secret)
    if IS_PRODUCTION:
        raise RuntimeError(
            "JWT_SECRET_KEY must be explicitly configured in production"
        )
    return _load_development_jwt_secret()


JWT_SECRET_KEY = _load_jwt_secret()

_COOKIE_SECURE_ENV = os.getenv("COOKIE_SECURE")
COOKIE_SECURE = (
    _COOKIE_SECURE_ENV.strip().lower() in {"1", "true", "yes"}
    if _COOKIE_SECURE_ENV is not None
    else IS_PRODUCTION
)
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", "").strip() or None
COOKIE_SAMESITE = os.getenv(
    "COOKIE_SAMESITE", "none" if IS_PRODUCTION else "lax"
).strip().lower()
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
    os.getenv(
        "PRIVATE_STORAGE_DIR",
        "/var/data/private"
        if IS_PRODUCTION
        else str(Path(__file__).resolve().parent / "private"),
    )
).resolve()
