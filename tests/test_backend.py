import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = Path(tempfile.mkdtemp(prefix="chattiebaby-tests-"))
TEST_DATABASE = TEST_ROOT / "app.db"
TEST_PRIVATE = TEST_ROOT / "private"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE.as_posix()}"
os.environ["JWT_SECRET_KEY"] = "tests-only-secret-key-with-at-least-32-bytes"
os.environ["PRIVATE_STORAGE_DIR"] = str(TEST_PRIVATE)
os.environ["CORS_ALLOW_ORIGINS"] = "http://localhost:5173"
os.environ["COOKIE_SECURE"] = "false"

from alembic import command
from alembic.config import Config


command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
with sqlite3.connect(TEST_DATABASE) as connection:
    connection.execute(
        "INSERT INTO users (id, username, email, password_hash) "
        "VALUES (1000000000, 'test_anchor', 'anchor@example.com', 'unused-test-hash')"
    )
    connection.execute(
        "INSERT INTO chats (id, user_id, platform, title, subtitle, theme) "
        "VALUES (1000000000, 1000000000, 'whatsapp', 'Test sequence anchor', '', 'light')"
    )

from fastapi.testclient import TestClient

from server.database import engine
from server.main import app


@pytest.fixture
def client():
    with TestClient(
        app,
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:5173"},
    ) as test_client:
        yield test_client


@pytest.fixture(scope="session", autouse=True)
def remove_test_outputs():
    yield
    with sqlite3.connect(TEST_DATABASE) as connection:
        rows = connection.execute(
            "SELECT id, platform FROM chats WHERE id >= 1000000000"
        ).fetchall()
    output_dir = ROOT / "server" / "output"
    prefixes = {"whatsapp": "chat_", "instagram": "instagram_", "chatgpt": "chatgpt_"}
    for chat_id, platform in rows:
        path = output_dir / f"{prefixes[platform]}{chat_id}.png"
        path.unlink(missing_ok=True)
    engine.dispose()
    shutil.rmtree(TEST_ROOT, ignore_errors=True)


def register(client: TestClient, label: str):
    unique = f"{label}_{uuid4().hex[:8]}"
    response = client.post(
        "/auth/register",
        json={
            "username": unique,
            "email": f"{unique}@example.com",
            "password": "correct horse battery staple",
        },
        headers=csrf_headers(client),
    )
    assert response.status_code == 201, response.text
    return response.json()


def csrf_headers(client: TestClient):
    csrf = client.cookies.get("chattiebaby_csrf")
    return {"X-CSRF-Token": csrf} if csrf else {}


def mutate(client: TestClient, method: str, url: str, **kwargs):
    headers = dict(kwargs.pop("headers", {}))
    headers.update(csrf_headers(client))
    return client.request(method, url, headers=headers, **kwargs)


def create_chat(client: TestClient, platform="whatsapp", **extra):
    response = mutate(
        client,
        "POST",
        "/chats",
        json={
            "platform": platform,
            "title": f"Test {platform}",
            "subtitle": "online",
            "theme": "light",
            "my_name": "Ari",
            "other_name": "Sam",
            "user_id": 999999999,
            **extra,
        },
    )
    assert response.status_code == 200, response.text
    assert "preview" not in response.json()
    return response.json()


def add_message(client: TestClient, chat_id: int, role="me"):
    response = mutate(
        client,
        "POST",
        f"/chats/{chat_id}/messages",
        json={
            "sender_role": role,
            "sender_id": 999999999,
            "type": "text",
            "content": "A generated message",
            "timestamp": "9:15 AM",
            "direction": "outbound" if role == "me" else "inbound",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["message_id"]


def test_auth_registration_login_rotation_logout_and_csrf(client):
    username = f"auth_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    payload = {"username": username, "email": email, "password": "correct horse battery staple"}

    preflight = client.options(
        "/auth/register",
        headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert preflight.headers["access-control-allow-credentials"] == "true"

    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert set(response.json()) == {"id", "username", "email", "created_at"}
    assert "password" not in response.text and "password_hash" not in response.text
    assert "token" not in response.text.lower()
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert len(set_cookie_headers) == 3
    access_cookie = next(value for value in set_cookie_headers if value.startswith("chattiebaby_access="))
    refresh_cookie = next(value for value in set_cookie_headers if value.startswith("chattiebaby_refresh="))
    csrf_cookie = next(value for value in set_cookie_headers if value.startswith("chattiebaby_csrf="))
    for cookie in (access_cookie, refresh_cookie, csrf_cookie):
        assert "Path=/" in cookie
        assert "SameSite=lax" in cookie
        assert "Domain=" not in cookie
        assert "Secure" not in cookie
    assert "HttpOnly" in access_cookie
    assert "HttpOnly" in refresh_cookie
    assert "HttpOnly" not in csrf_cookie
    assert "Max-Age=900" in access_cookie
    assert "Max-Age=" in refresh_cookie
    assert "Max-Age=" in csrf_cookie
    assert client.cookies.get("chattiebaby_access")
    assert client.cookies.get("chattiebaby_refresh")
    assert client.cookies.get("chattiebaby_csrf")
    assert client.get("/auth/me").status_code == 200
    assert client.get("/settings/me").status_code == 200
    created = create_chat(client, "whatsapp")
    assert client.get("/chats").json()[0]["id"] == created["chat_id"]

    csrf = client.cookies.get("chattiebaby_csrf")
    assert client.post("/settings/me", json={"theme": "dark"}).status_code == 403
    assert client.post(
        "/settings/me",
        json={"theme": "dark"},
        headers={"X-CSRF-Token": "invalid-csrf-token"},
    ).status_code == 403
    assert client.post(
        "/auth/logout",
        headers={"X-CSRF-Token": csrf, "Origin": "https://attacker.example"},
    ).status_code == 403

    old_refresh = client.cookies.get("chattiebaby_refresh")
    rotated = mutate(client, "POST", "/auth/refresh")
    assert rotated.status_code == 200, rotated.text
    new_refresh = client.cookies.get("chattiebaby_refresh")
    assert old_refresh and new_refresh and old_refresh != new_refresh

    assert client.get("/auth/me").status_code == 200
    assert client.get("/settings/me").status_code == 200
    assert client.get("/chats").status_code == 200

    refresh_after_rotation = client.cookies.get("chattiebaby_refresh")
    csrf_after_rotation = client.cookies.get("chattiebaby_csrf")
    old_session = TestClient(
        app,
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:5173"},
    )
    old_session.cookies.set("chattiebaby_refresh", old_refresh)
    old_session.cookies.set("chattiebaby_csrf", client.cookies.get("chattiebaby_csrf"))
    replay = old_session.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": old_session.cookies.get("chattiebaby_csrf")},
    )
    assert replay.status_code == 401
    old_session.close()

    assert mutate(client, "POST", "/auth/logout").status_code == 200
    assert all(
        client.cookies.get(name) is None
        for name in (
            "chattiebaby_access",
            "chattiebaby_refresh",
            "chattiebaby_csrf",
        )
    )
    assert client.get("/auth/me").status_code == 401
    logged_out_session = TestClient(
        app,
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:5173"},
    )
    logged_out_session.cookies.set("chattiebaby_refresh", refresh_after_rotation)
    logged_out_session.cookies.set("chattiebaby_csrf", csrf_after_rotation)
    revoked_refresh = logged_out_session.post(
        "/auth/refresh",
        headers={"X-CSRF-Token": csrf_after_rotation},
    )
    assert revoked_refresh.status_code == 401
    logged_out_session.close()

    login = client.post("/auth/login", json={"identifier": email, "password": payload["password"]})
    assert login.status_code == 200, login.text
    assert len(login.headers.get_list("set-cookie")) == 3
    assert client.get("/auth/me").status_code == 200
    assert login.json()["username"] == username.lower()
    assert mutate(
        client,
        "POST",
        "/auth/login",
        json={"identifier": username, "password": "not the password"},
    ).status_code == 401


def test_unauthenticated_account_requests_return_401():
    with TestClient(
        app,
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:5173"},
    ) as unauthenticated:
        for path in ("/auth/me", "/settings/me", "/chats", "/history"):
            assert unauthenticated.get(path).status_code == 401


def test_production_cookies_are_secure_by_default():
    env = os.environ.copy()
    env.pop("COOKIE_SECURE", None)
    env["APP_ENV"] = "production"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from server.config import COOKIE_SECURE; assert COOKIE_SECURE",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0
    env["COOKIE_SECURE"] = "false"
    rejected = subprocess.run(
        [
            sys.executable,
            "-c",
            "from server.config import COOKIE_SECURE",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert rejected.returncode != 0


def test_development_jwt_secret_is_generated_and_reused(tmp_path):
    secret_file = tmp_path / ".secrets" / "jwt_secret"
    env = os.environ.copy()
    env.pop("JWT_SECRET_KEY", None)
    env["APP_ENV"] = "development"
    env["JWT_SECRET_FILE"] = str(secret_file)
    script = "from server.config import JWT_SECRET_KEY; print(JWT_SECRET_KEY)"

    first = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    second = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert first.stdout.strip() == second.stdout.strip()
    assert len(first.stdout.strip().encode("utf-8")) >= 32
    assert secret_file.read_text(encoding="utf-8") == first.stdout.strip()
    if os.name != "nt":
        assert secret_file.stat().st_mode & 0o777 == 0o600


def test_explicit_jwt_secret_takes_precedence(tmp_path):
    secret_file = tmp_path / ".secrets" / "jwt_secret"
    secret_file.parent.mkdir()
    secret_file.write_text("persisted-secret-with-at-least-32-bytes", encoding="utf-8")
    env = os.environ.copy()
    env["APP_ENV"] = "development"
    env["JWT_SECRET_FILE"] = str(secret_file)
    env["JWT_SECRET_KEY"] = "explicit-secret-with-at-least-32-bytes"

    result = subprocess.run(
        [sys.executable, "-c", "from server.config import JWT_SECRET_KEY; print(JWT_SECRET_KEY)"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == env["JWT_SECRET_KEY"]
    assert secret_file.read_text(encoding="utf-8") == "persisted-secret-with-at-least-32-bytes"


@pytest.mark.parametrize(
    ("app_env", "secret", "message"),
    [
        ("development", "too-short", "JWT_SECRET_KEY must contain at least 32 bytes"),
        ("production", None, "JWT_SECRET_KEY must be explicitly configured in production"),
        ("production", "too-short", "JWT_SECRET_KEY must contain at least 32 bytes"),
    ],
)
def test_jwt_secret_validation(app_env, secret, message, tmp_path):
    env = os.environ.copy()
    env["APP_ENV"] = app_env
    env["JWT_SECRET_FILE"] = str(tmp_path / "jwt_secret")
    if app_env in {"production", "prod"}:
        env["COOKIE_SECURE"] = "true"
    if secret is None:
        env.pop("JWT_SECRET_KEY", None)
    else:
        env["JWT_SECRET_KEY"] = secret

    result = subprocess.run(
        [sys.executable, "-c", "from server.config import JWT_SECRET_KEY"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert message in result.stderr


def test_profile_settings_password_and_account_deletion(client):
    user = register(client, "profile")
    response = mutate(
        client,
        "PATCH",
        "/users/me",
        json={"username": f"updated_{uuid4().hex[:8]}", "email": f"updated_{uuid4().hex[:8]}@example.com"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["id"] == user["id"]

    settings = mutate(
        client,
        "PATCH",
        "/settings/me",
        json={"theme": "dark", "preferences": {"layout": "compact"}},
    )
    assert settings.status_code == 200
    assert settings.json() == {"theme": "dark", "preferences": {"layout": "compact"}}
    assert client.get("/settings/me").json()["theme"] == "dark"

    password_change = mutate(
        client,
        "PATCH",
        "/users/me/password",
        json={
            "current_password": "correct horse battery staple",
            "new_password": "another correct horse battery",
        },
    )
    assert password_change.status_code == 200
    assert client.get("/auth/me").status_code == 401
    assert client.post(
        "/auth/login",
        json={"identifier": user["username"], "password": "correct horse battery staple"},
    ).status_code == 401
    login = client.post(
        "/auth/login",
        json={"identifier": response.json()["email"], "password": "another correct horse battery"},
    )
    assert login.status_code == 200, login.text

    created = create_chat(client, "whatsapp")
    user_storage = TEST_PRIVATE / "generated" / str(user["id"])
    assert user_storage.is_dir()

    wrong_password = mutate(
        client, "DELETE", "/users/me", json={"password": "incorrect password"}
    )
    assert wrong_password.status_code == 400
    deleted = mutate(
        client,
        "DELETE",
        "/users/me",
        json={"password": "another correct horse battery"},
    )
    assert deleted.status_code == 204
    assert client.get("/auth/me").status_code == 401
    assert not user_storage.exists()
    with sqlite3.connect(TEST_DATABASE) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM chats WHERE id = ?", (created["chat_id"],)
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM user_settings WHERE user_id = ?", (user["id"],)
        ).fetchone()[0] == 0


def test_chat_message_participant_preview_history_and_pillow_renderers(client):
    register(client, "generator")
    for platform in ("whatsapp", "instagram", "chatgpt"):
        created = create_chat(client, platform)
        chat_id = created["chat_id"]
        message_id = add_message(client, chat_id)
        preview = client.get(f"/chats/{chat_id}/preview")
        assert preview.status_code == 200
        assert preview.headers["content-type"] == "image/png"
        assert preview.content.startswith(b"\x89PNG\r\n\x1a\n")

        image = Image.open(BytesIO(preview.content))
        assert image.width == 1080 and image.height >= 1200

        detail = client.get(f"/chats/{chat_id}/data")
        assert detail.status_code == 200
        assert detail.json()["messages"][0]["content"] == "A generated message"
        assert client.get("/chats").json()[0]["id"] == chat_id
        assert client.get("/history").json() == []
        updated_chat = mutate(
            client,
            "PATCH",
            f"/chats/{chat_id}",
            json={"title": "Updated conversation", "subtitle": "available"},
        )
        assert updated_chat.status_code == 200
        assert client.get(f"/chats/{chat_id}/data").json()["title"] == "Updated conversation"

        generated = mutate(client, "POST", f"/chats/{chat_id}/generate")
        assert generated.status_code == 200
        assert generated.headers["content-type"] == "image/png"
        assert generated.content.startswith(b"\x89PNG\r\n\x1a\n")
        second_generation = mutate(client, "POST", f"/chats/{chat_id}/generate")
        assert second_generation.status_code == 200
        assert len([item for item in client.get("/history").json() if item["chat_id"] == chat_id]) == 2

        changed = mutate(
            client,
            "PATCH",
            f"/chats/{chat_id}/messages/{message_id}",
            json={"content": "Edited text", "timestamp": "9:20 AM"},
        )
        assert changed.status_code == 200
        assert mutate(client, "DELETE", f"/chats/{chat_id}/messages/{message_id}").status_code == 200

        uploaded = Image.new("RGB", (20, 20), color="green")
        upload_data = BytesIO()
        uploaded.save(upload_data, format="PNG")
        participant_id = created["other_id"]
        bad_upload = mutate(
            client,
            "POST",
            f"/participants/{participant_id}/avatar",
            files={"file": ("bad.png", b"not an image", "image/png")},
        )
        assert bad_upload.status_code == 400
        upload_data.seek(0)
        avatar = mutate(
            client,
            "POST",
            f"/participants/{participant_id}/avatar",
            files={"file": ("avatar.png", upload_data, "image/png")},
        )
        assert avatar.status_code == 200
        assert "path" not in avatar.text.lower()
        assert client.get(f"/participants/{participant_id}/avatar").status_code == 200
        with sqlite3.connect(TEST_DATABASE) as connection:
            avatar_path = Path(
                connection.execute(
                    "SELECT avatar_path FROM participants WHERE id = ?", (participant_id,)
                ).fetchone()[0]
            )
        assert avatar_path.is_file()

        history = client.get("/history").json()
        matching = [item for item in history if item["chat_id"] == chat_id]
        assert len(matching) == 2
        assert client.get(matching[0]["image_url"]).content.startswith(b"\x89PNG\r\n\x1a\n")
        assert mutate(client, "DELETE", f"/history/{matching[0]['id']}").status_code == 204
        assert client.get(f"/history/{matching[0]['id']}/image").status_code == 404
        assert client.get(f"/history/{matching[1]['id']}/image").status_code == 200

        extra = mutate(
            client,
            "POST",
            f"/participants/chats/{chat_id}",
            json={"name": "Third person", "role": "other"},
        )
        assert extra.status_code == 201
        participant_id = extra.json()["id"]
        assert mutate(
            client,
            "PATCH",
            f"/participants/{participant_id}",
            json={"name": "Updated name"},
        ).status_code == 200
        assert mutate(client, "DELETE", f"/participants/{participant_id}").status_code == 204

        assert mutate(client, "DELETE", f"/chats/{chat_id}").status_code == 204
        assert client.get(f"/chats/{chat_id}/preview").status_code == 404
        assert client.get(f"/chats/{chat_id}/data").status_code == 404
        assert client.get(f"/history/{matching[1]['id']}/image").status_code == 404
        assert not avatar_path.exists()


def test_cross_user_resource_access_is_denied(client):
    register(client, "owner")
    created = create_chat(client, "instagram")
    chat_id = created["chat_id"]
    message_id = add_message(client, chat_id)
    image = Image.new("RGB", (8, 8), "red")
    data = BytesIO()
    image.save(data, format="PNG")
    data.seek(0)
    uploaded = mutate(
        client,
        "POST",
        f"/participants/{created['other_id']}/avatar",
        files={"file": ("private.png", data, "image/png")},
    )
    assert uploaded.status_code == 200
    assert mutate(client, "POST", f"/chats/{chat_id}/generate").status_code == 200
    history_id = next(item["id"] for item in client.get("/history").json() if item["chat_id"] == chat_id)

    register(client, "different")
    assert client.get("/chats").json() == []
    assert client.get(f"/chats/{chat_id}/data").status_code == 404
    assert client.get(f"/chats/{chat_id}/preview").status_code == 404
    assert client.get(f"/chats/{chat_id}/messages").status_code == 404
    assert client.get(f"/participants/{created['other_id']}/avatar").status_code == 404
    assert client.get(f"/history/{history_id}/image").status_code == 404
    assert mutate(client, "PATCH", f"/chats/{chat_id}", json={"title": "stolen"}).status_code == 404
    assert mutate(
        client,
        "PATCH",
        f"/chats/{chat_id}/messages/{message_id}",
        json={"content": "stolen", "timestamp": "9:20"},
    ).status_code == 404
    assert mutate(client, "DELETE", f"/chats/{chat_id}").status_code == 404
    assert mutate(client, "DELETE", f"/history/{history_id}").status_code == 404


def test_fresh_migration_creates_empty_constrained_schema(tmp_path):
    database = tmp_path / "fresh.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{database.resolve().as_posix()}"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "alembic.ini"),
            "upgrade",
            "head",
        ],
        cwd=ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert {
            "users",
            "user_settings",
            "chats",
            "participants",
            "messages",
            "generation_history",
            "refresh_sessions",
            "alembic_version",
        } == tables
        for table in (
            "users",
            "user_settings",
            "chats",
            "participants",
            "messages",
            "generation_history",
            "refresh_sessions",
        ):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0

        chat_columns = {
            row[1]: row[3] for row in connection.execute("PRAGMA table_info(chats)")
        }
        message_columns = {
            row[1]: row[3] for row in connection.execute("PRAGMA table_info(messages)")
        }
        assert chat_columns["user_id"] == 1
        assert message_columns["sender_id"] == 1
        assert {"ix_users_username", "ix_users_email"}.issubset(
            {row[1] for row in connection.execute("PRAGMA index_list(users)")}
        )
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone()[0] == "20261101_0001"
