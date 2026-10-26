import sqlite3

import pytest

from app.db.migrate import migrate_down, migrate_up


def test_unknown_route_uses_error_format(client):
    r = client.get("/v1/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_method_not_allowed_uses_error_format(client):
    r = client.put("/v1/meals")
    assert r.status_code == 405
    assert set(r.json()["error"]) == {"code", "message", "details"}


ALL = [
    "0001_init",
    "0002_privacy_consent",
    "0003_one_identity_per_provider",
]


def test_migrations_up_down_up(tmp_path):
    conn = sqlite3.connect(tmp_path / "m.db", isolation_level=None)

    def cols(table):
        return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}

    def indexes():
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")}

    assert migrate_up(conn) == ALL
    assert migrate_up(conn) == []
    assert "consented_at" in cols("users")
    assert "uq_auth_identities_user_provider" in indexes()
    assert migrate_down(conn) == "0003_one_identity_per_provider"
    assert "uq_auth_identities_user_provider" not in indexes()
    assert migrate_down(conn) == "0002_privacy_consent"
    assert "consented_at" not in cols("users")
    assert migrate_down(conn) == "0001_init"
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "meals" not in tables
    assert migrate_up(conn) == ALL
    conn.close()


def _identity(conn, email, user_id="u1"):
    conn.execute(
        "INSERT INTO auth_identities (provider, identifier, user_id, secret_hash, created_at) "
        "VALUES ('password', ?, ?, 'h', 't')",
        (email, user_id),
    )


def test_migration_0003_keeps_first_identity_and_enforces_one_per_provider(tmp_path):
    conn = sqlite3.connect(tmp_path / "m.db", isolation_level=None)
    migrate_up(conn)
    migrate_down(conn)  # back to 0002: duplicates are still possible here
    conn.execute("INSERT INTO users (id, timezone, created_at) VALUES ('u1', 'UTC', 't')")
    for email in ("first@example.com", "second@example.com", "third@example.com"):
        _identity(conn, email)
    assert migrate_up(conn) == ALL[2:]
    rows = conn.execute("SELECT identifier FROM auth_identities").fetchall()
    assert rows == [("first@example.com",)]
    with pytest.raises(sqlite3.IntegrityError):
        _identity(conn, "fourth@example.com")
    conn.close()
