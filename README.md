# ChattieBaby

ChattieBaby creates fictional chat screenshots. The React/Vite client calls a FastAPI API; platform-specific Pillow renderers generate PNGs. SQLite stores accounts, settings, chats, messages, participants, refresh sessions, and generation history.

## Local setup and database reset (PowerShell)

From the repository root (`E:\chatMemeGenerator`), install dependencies once:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm --prefix client install
```

The explicit reset command permanently deletes only the repository-local ChattieBaby `mockchat.db`, its SQLite sidecars, app-private generated images/avatars, uploaded avatars, and renderer PNG outputs:

```powershell
Set-Location E:\chatMemeGenerator
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:PRIVATE_STORAGE_DIR -ErrorAction SilentlyContinue
.\venv\Scripts\python.exe -m server.reset_database --yes
.\venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
```

The reset tool is intentionally restricted: it requires the project root and `--yes`, refuses configured database/storage overrides, verifies the target is a healthy SQLite file containing ChattieBaby chat tables, and refuses symlinks or paths outside this repository. It does not connect to, drop, or modify any remote or unrelated database. Reset is never run automatically at application startup. For a deployed environment, provision a new empty database dedicated to ChattieBaby and run Alembic against that explicit deployment URL; do not point the local reset tool at it.

The default database URL is `sqlite:///./mockchat.db`, resolved from the repository root. The fresh initial migration creates the schema; it does not transform legacy tables.

### Start the API

In a PowerShell terminal at the repository root:

```powershell
Set-Location E:\chatMemeGenerator
$env:APP_ENV = "development"
$env:DATABASE_URL = "sqlite:///./mockchat.db"
$env:JWT_SECRET_KEY = "local-development-secret-change-this-to-a-random-32-byte-value"
$env:CORS_ALLOW_ORIGINS = "http://localhost:5173"
$env:COOKIE_SECURE = "false"
$env:COOKIE_SAMESITE = "lax"
Remove-Item Env:COOKIE_DOMAIN -ErrorAction SilentlyContinue
.\venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\venv\Scripts\python.exe -m uvicorn server.main:app --reload --host 127.0.0.1 --port 8000
```

### Start the frontend

In a second PowerShell terminal:

```powershell
Set-Location E:\chatMemeGenerator
npm --prefix client run dev -- --host localhost
```

Open `http://localhost:5173`. `client/.env.development.local` points the development frontend at `http://localhost:8000`. Keep the hostname identical (`localhost`) on both sides: browser cookies are host-scoped, while `localhost` and `127.0.0.1` are different cookie hosts and different sites for `SameSite` checks. Ports make the frontend/API cross-origin, so the API allows the exact frontend origin with credentialed CORS. `SameSite=Lax` remains enabled, `Secure` is disabled only for local HTTP development, the cookie domain is host-only, and the CSRF cookie/header check stays enabled. Restart Vite after changing its environment files.

## API areas

| Router | Main routes |
|---|---|
| `auth` | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`; `GET /auth/me` |
| `users` | `GET/PATCH/DELETE /users/me`; `PATCH /users/me/password` |
| `settings` | `GET/PATCH /settings/me` |
| `chats` | `GET/POST /chats`; `GET/PATCH/DELETE /chats/{id}`; `GET /chats/{id}/data` and `/preview`; `POST /chats/{id}/generate` |
| `participants` | List/create by chat, update/delete by participant, upload/read private avatar |
| `messages` | List/create by chat; update/delete by message |
| `history` | List/delete history entries and read private generated images |
| `examples` | List fictional examples and read their public PNGs |

All private chat, participant, message, avatar, history, and generated-image access is scoped to the authenticated user. Request and response schemas are defined with Pydantic.
Preview requests do not create history entries; each explicit `POST /chats/{id}/generate` creates a separately downloadable, owner-private history record.

## Database schema

- `users`: username, email, password hash, creation time.
- `user_settings`: per-user theme and JSON preferences.
- `chats`: platform and conversation metadata; every chat has a required owner.
- `participants`: chat-owned names, roles, and private avatar paths.
- `messages`: chat-owned text, type, timestamp, ordering, direction, required participant sender, optional reply, and metadata.
- `generation_history`: user/chat association and private output path.
- `refresh_sessions`: user association, hashed refresh token, expiry, and revocation time.

The ORM relationships use foreign keys, ownership constraints, indexes, and delete cascades. The initial Alembic migration creates all seven tables and checks SQLite foreign-key consistency. Because this is a fresh schema, existing databases must be reset or replaced with a new empty database before upgrading.

## Configuration and deployment

Required in production:

- `JWT_SECRET_KEY`: stable secret of at least 32 bytes.
- `CORS_ALLOW_ORIGINS`: comma-separated explicit frontend origins (wildcard origins are rejected).
- `DATABASE_URL`: persistent database URL; the default is a working-directory-relative SQLite file.
- `PRIVATE_STORAGE_DIR`: persistent, non-public storage for generated images and avatars.
- `COOKIE_SECURE=true` behind HTTPS. For cross-site frontend/API hosting, configure `COOKIE_SAMESITE=none`, `COOKIE_SECURE=true`, and an appropriate `COOKIE_DOMAIN`; browser third-party-cookie policies may still block such deployments.

`COOKIE_SECURE` defaults to `true` when `APP_ENV=production` (and `false` for development). Production HTTPS deployments must not set it to `false`. The frontend and API should be same-site where possible; cross-site deployments can also be affected by third-party-cookie restrictions.

Docker applies `alembic upgrade head` before starting Uvicorn. Point deployment at a new, empty, ChattieBaby-dedicated database for the first deployment of this schema. Email-based password reset is not implemented; signed-in users can change their password from account settings.

## Verification

```powershell
.\venv\Scripts\python.exe -m pytest -q
npm --prefix client run build
npm --prefix client run lint
git diff --check
```
