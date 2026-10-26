import sqlite3

from app.db.migrate import migrate_down, migrate_up


def test_unknown_route_uses_error_format(client):
    r = client.get("/v1/nope")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_method_not_allowed_uses_error_format(client):
    r = client.put("/v1/meals")
    assert r.status_code == 405
    assert set(r.json()["error"]) == {"code", "message", "details"}


def test_migrations_up_down_up(tmp_path):
    conn = sqlite3.connect(tmp_path / "m.db", isolation_level=None)
    assert migrate_up(conn) == ["0001_init"]
    assert migrate_up(conn) == []
    assert migrate_down(conn) == "0001_init"
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "meals" not in tables
    assert migrate_up(conn) == ["0001_init"]
    conn.close()
