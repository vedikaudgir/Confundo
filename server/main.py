import hmac
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from server.config import (
    ACCESS_COOKIE,
    APP_ENV,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    CSRF_COOKIE,
    JWT_SECRET_KEY,
    REFRESH_COOKIE,
)
from server.repositories.__init__db import init_db
from server.routers import (
    auth,
    chats,
    examples,
    history,
    messages,
    participants,
    settings,
    users,
)


def _cors_origins():
    raw = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "https://confundo.vercel.app"
        if APP_ENV in {"production", "prod"}
        else "http://localhost:5173",
    )
    origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    if not origins or "*" in origins:
        raise ValueError("CORS_ALLOW_ORIGINS must contain explicit browser origins")
    return origins


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if len(JWT_SECRET_KEY.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 bytes")
    if COOKIE_SAMESITE == "none" and not COOKIE_SECURE:
        raise RuntimeError("COOKIE_SECURE must be true when COOKIE_SAMESITE is none")
    init_db()
    yield


api = FastAPI(title="ChattieBaby", lifespan=lifespan)


@api.middleware("http")
async def protect_cookie_authenticated_writes(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        has_cookie_session = bool(
            request.cookies.get(ACCESS_COOKIE) or request.cookies.get(REFRESH_COOKIE)
        )
        has_bearer = request.headers.get("authorization", "").lower().startswith("bearer ")
        if has_cookie_session and not has_bearer:
            csrf_cookie = request.cookies.get(CSRF_COOKIE, "")
            csrf_header = request.headers.get("x-csrf-token", "")
            allowed_origins = _cors_origins()
            origin = request.headers.get("origin")
            if (
                not csrf_cookie
                or not csrf_header
                or not hmac.compare_digest(csrf_cookie, csrf_header)
                or (origin is not None and origin.rstrip("/") not in allowed_origins)
            ):
                return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})
    return await call_next(request)


for router in (
    auth.router,
    users.router,
    settings.router,
    chats.router,
    participants.router,
    messages.router,
    history.router,
    examples.router,
):
    api.include_router(router)


app = CORSMiddleware(
    app=api,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization"],
    expose_headers=["X-CSRF-Token"],
)
