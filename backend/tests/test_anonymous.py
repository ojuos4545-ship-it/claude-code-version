"""Anonymous start, account linking, sliding sessions and privacy consent (PRD Q4, Q6)."""

import sqlite3

from tests.conftest import create_meal


def start(client, **extra):
    r = client.post("/v1/auth/anonymous", json={"privacy_consent": True, **extra})
    assert r.status_code == 201, r.text
    body = r.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body


def test_anonymous_start_needs_only_consent(client):
    h, body = start(client, timezone="Europe/Paris")
    assert body["user"]["email"] is None
    assert body["user"]["timezone"] == "Europe/Paris"
    create_meal(client, h)
    me = client.get("/v1/me", headers=h).json()
    assert me["email"] is None


def test_consent_is_required_and_recorded(client, settings):
    for body in ({}, {"privacy_consent": False}):
        r = client.post("/v1/auth/anonymous", json=body)
        assert r.status_code == 422
        assert r.json()["error"]["details"][0]["field"] == "privacy_consent"
    _, body = start(client)
    conn = sqlite3.connect(settings.database_path)
    (consented_at,) = conn.execute(
        "SELECT consented_at FROM users WHERE id = ?", (body["user"]["id"],)
    ).fetchone()
    conn.close()
    assert consented_at == body["user"]["created_at"]


def test_link_password_keeps_meals_and_enables_login(client):
    h, body = start(client)
    create_meal(client, h, description="김밥")
    r = client.post(
        "/v1/auth/link", json={"email": "Linked@Example.com", "password": "linked-pass"}, headers=h
    )
    assert r.status_code == 200
    assert r.json()["email"] == "linked@example.com"
    login = client.post(
        "/v1/auth/login", json={"email": "linked@example.com", "password": "linked-pass"}
    ).json()
    assert login["user"]["id"] == body["user"]["id"]
    h2 = {"Authorization": f"Bearer {login['access_token']}"}
    recent = client.get("/v1/meals/recent-descriptions", headers=h2).json()["items"]
    assert recent == ["김밥"]


def test_link_conflicts(client, alice):
    h, _ = start(client)
    taken = client.post(
        "/v1/auth/link", json={"email": "alice@example.com", "password": "whatever1"}, headers=h
    )
    assert taken.status_code == 409
    again = client.post(
        "/v1/auth/link", json={"email": "other@example.com", "password": "whatever1"}, headers=alice
    )
    assert again.status_code == 409
    assert (
        client.post("/v1/auth/link", json={"email": "a@b.co", "password": "x"}).status_code == 401
    )


def test_anonymous_user_deletes_without_password(client, settings):
    h, body = start(client)
    create_meal(client, h)
    assert client.request("DELETE", "/v1/me", headers=h).status_code == 204
    assert client.get("/v1/me", headers=h).status_code == 401
    conn = sqlite3.connect(settings.database_path)
    left = conn.execute("SELECT COUNT(*) FROM meals").fetchone()[0]
    conn.close()
    assert left == 0


def test_session_slides_while_in_use_and_expires_when_idle(client, clock):
    h, _ = start(client)
    # Used every 20 days: never expires even though the lifetime is 30 days.
    for _ in range(4):
        clock.advance(days=20)
        assert client.get("/v1/me", headers=h).status_code == 200
    # Left unused for longer than the lifetime: expires.
    clock.advance(days=31)
    assert client.get("/v1/me", headers=h).status_code == 401
