"""FR-6: delete account and all data atomically."""

import sqlite3

from app.repositories.sqlite import SqliteRepository
from tests.conftest import create_meal, signup


def _count(db_path, sql, *params):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(sql, params).fetchone()[0]
    finally:
        conn.close()


def _me_id(client, h):
    return client.get("/v1/me", headers=h).json()["id"]


def test_delete_account_removes_user_meals_and_sessions(client, settings, bob):
    h = signup(client, "leaver@example.com", password="leaver-password")
    second = client.post(
        "/v1/auth/login", json={"email": "leaver@example.com", "password": "leaver-password"}
    ).json()["access_token"]
    uid = _me_id(client, h)
    create_meal(client, h, description="a", portion="small")
    create_meal(client, h, description="b", meal_date="2026-10-20")
    create_meal(client, bob, description="bob keeps this")

    r = client.request("DELETE", "/v1/me", json={"password": "leaver-password"}, headers=h)
    assert r.status_code == 204

    # no token of that account works any more
    for token_headers in (h, {"Authorization": f"Bearer {second}"}):
        assert client.get("/v1/me", headers=token_headers).status_code == 401
        assert client.get("/v1/meals?date=2026-10-26", headers=token_headers).status_code == 401
        assert (
            client.post("/v1/meals", json={"description": "x"}, headers=token_headers).status_code
            == 401
        )
    login = client.post(
        "/v1/auth/login", json={"email": "leaver@example.com", "password": "leaver-password"}
    )
    assert login.status_code == 401

    db = settings.database_path
    assert _count(db, "SELECT COUNT(*) FROM users WHERE id = ?", uid) == 0
    assert _count(db, "SELECT COUNT(*) FROM meals WHERE user_id = ?", uid) == 0
    assert _count(db, "SELECT COUNT(*) FROM sessions WHERE user_id = ?", uid) == 0
    assert _count(db, "SELECT COUNT(*) FROM auth_identities WHERE user_id = ?", uid) == 0
    # other users are unaffected
    assert [
        m["description"]
        for m in client.get("/v1/meals?date=2026-10-26", headers=bob).json()["items"]
    ] == ["bob keeps this"]


def test_email_can_sign_up_again_with_no_old_data(client):
    h = signup(client, "again@example.com", password="password-1")
    create_meal(client, h)
    client.request("DELETE", "/v1/me", json={"password": "password-1"}, headers=h)
    h2 = signup(client, "again@example.com", password="password-2")
    assert client.get("/v1/meals?date=2026-10-26", headers=h2).json()["items"] == []


def test_wrong_password_keeps_everything(client, alice):
    meal = create_meal(client, alice)
    r = client.request("DELETE", "/v1/me", json={"password": "wrong"}, headers=alice)
    assert r.status_code == 403
    assert client.get(f"/v1/meals/{meal['id']}", headers=alice).status_code == 200


def test_password_user_must_confirm_password(client, alice):
    # Omitting the password is allowed only for users who have none (anonymous).
    assert client.request("DELETE", "/v1/me", json={}, headers=alice).status_code == 403
    assert client.request("DELETE", "/v1/me", headers=alice).status_code == 403
    assert client.get("/v1/me", headers=alice).status_code == 200


def test_failure_midway_rolls_back_everything(client, settings, monkeypatch):
    h = signup(client, "atomic@example.com", password="atomic-pass")
    uid = _me_id(client, h)
    create_meal(client, h)
    create_meal(client, h)

    def boom(self, user_id):
        raise RuntimeError("disk on fire")

    # sessions, meals and login methods are deleted first, then deleting the user fails
    monkeypatch.setattr(SqliteRepository, "delete_user", boom)
    r = client.request("DELETE", "/v1/me", json={"password": "atomic-pass"}, headers=h)
    assert r.status_code == 500
    assert r.json() == {
        "error": {"code": "internal_error", "message": "Internal server error.", "details": []}
    }
    assert "disk on fire" not in r.text

    db = settings.database_path
    assert _count(db, "SELECT COUNT(*) FROM users WHERE id = ?", uid) == 1
    assert _count(db, "SELECT COUNT(*) FROM meals WHERE user_id = ?", uid) == 2
    assert _count(db, "SELECT COUNT(*) FROM auth_identities WHERE user_id = ?", uid) == 1
    monkeypatch.undo()
    assert client.get("/v1/me", headers=h).status_code == 200  # session also intact
