"""Auth basics (minimal, replaceable implementation for FR-1)."""

import sqlite3

import pytest

from app.config import ConfigError, load_settings
from tests.conftest import signup


def test_signup_returns_token_usable_for_me(client):
    r = client.post(
        "/v1/auth/signup", json={"email": " New@Example.com ", "password": "longenough1"}
    )
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["timezone"] == "Asia/Seoul"
    assert body["token_type"] == "bearer"
    me = client.get("/v1/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["id"] == body["user"]["id"]


def test_password_is_stored_as_argon2_hash(client, settings):
    signup(client, "hash@example.com", password="plain-password-9")
    conn = sqlite3.connect(settings.database_path)
    (stored,) = conn.execute("SELECT secret_hash FROM auth_identities").fetchone()
    conn.close()
    assert stored.startswith("$argon2")
    assert "plain-password-9" not in stored


def test_user_identity_is_separate_from_login_method(client, settings):
    h = signup(client, "split@example.com")
    uid = client.get("/v1/me", headers=h).json()["id"]
    conn = sqlite3.connect(settings.database_path)
    user_cols = {r[1] for r in conn.execute("PRAGMA table_info(users)")}
    identity = conn.execute(
        "SELECT provider, identifier, user_id FROM auth_identities WHERE user_id = ?", (uid,)
    ).fetchone()
    conn.close()
    assert user_cols == {"id", "timezone", "created_at"}
    assert identity == ("password", "split@example.com", uid)


def test_auth_uses_header_not_cookies(client):
    r = client.post("/v1/auth/signup", json={"email": "c@example.com", "password": "abcdefgh"})
    assert "set-cookie" not in r.headers
    client.cookies.clear()
    assert client.get("/v1/me").status_code == 401


def test_duplicate_email_conflicts(client):
    signup(client, "dup@example.com")
    r = client.post("/v1/auth/signup", json={"email": "DUP@example.com", "password": "abcdefgh"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "conflict"


@pytest.mark.parametrize(
    "body, field",
    [
        ({"email": "not-an-email", "password": "abcdefgh"}, "email"),
        ({"email": "a@b.co", "password": "short"}, "password"),
        ({"email": "a@b.co", "password": "abcdefgh", "timezone": "Mars/Base"}, "timezone"),
        ({"email": "a@b.co", "password": "abcdefgh", "weight": 70}, "weight"),
    ],
)
def test_signup_validation(client, body, field):
    r = client.post("/v1/auth/signup", json=body)
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    assert [d["field"] for d in err["details"]] == [field]


def test_validation_error_does_not_echo_password(client):
    r = client.post("/v1/auth/signup", json={"email": "x@y.zz", "password": "secret1"})
    assert r.status_code == 422
    assert "secret1" not in r.text


def test_login(client):
    signup(client, "login@example.com", password="right-password")
    ok = client.post(
        "/v1/auth/login", json={"email": "login@example.com", "password": "right-password"}
    )
    assert ok.status_code == 200
    assert ok.json()["access_token"]
    bad = client.post(
        "/v1/auth/login", json={"email": "login@example.com", "password": "wrong-pass"}
    )
    unknown = client.post("/v1/auth/login", json={"email": "nobody@example.com", "password": "x"})
    assert bad.status_code == unknown.status_code == 401
    assert bad.json() == unknown.json()  # does not reveal whether the email exists


def test_logout_revokes_token(client):
    h = signup(client)
    assert client.post("/v1/auth/logout", headers=h).status_code == 204
    assert client.get("/v1/me", headers=h).status_code == 401


def test_expired_token_rejected(client, clock, settings):
    h = signup(client)
    clock.advance(seconds=settings.token_ttl_seconds + 1)
    r = client.get("/v1/me", headers=h)
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_update_timezone(client):
    h = signup(client)
    r = client.patch("/v1/me", json={"timezone": "America/New_York"}, headers=h)
    assert r.status_code == 200
    assert r.json()["timezone"] == "America/New_York"
    assert client.patch("/v1/me", json={"timezone": "Nope/Zone"}, headers=h).status_code == 422


def test_production_requires_secret_key():
    with pytest.raises(ConfigError):
        load_settings({"APP_ENV": "production"})
    with pytest.raises(ConfigError):
        load_settings({"APP_SECRET_KEY": "too-short"})
    s = load_settings({"APP_SECRET_KEY": "x" * 40})
    assert s.env == "production"
    assert s.secret_key == "x" * 40
    assert load_settings({"APP_ENV": "development"}).is_dev


def test_cors_origin_settings():
    dev = load_settings({"APP_ENV": "development"})
    assert dev.cors_origins and all("localhost" in o or "127.0.0.1" in o for o in dev.cors_origins)
    assert load_settings({"APP_SECRET_KEY": "x" * 40}).cors_origins == ()
    prod = load_settings(
        {
            "APP_SECRET_KEY": "x" * 40,
            "APP_CORS_ORIGINS": "https://a.example.com/, https://b.io:8443",
        }
    )
    assert prod.cors_origins == ("https://a.example.com", "https://b.io:8443")
    for bad in ["*", "https://a.com/path", "a.com"]:
        with pytest.raises(ConfigError):
            load_settings({"APP_ENV": "development", "APP_CORS_ORIGINS": bad})
