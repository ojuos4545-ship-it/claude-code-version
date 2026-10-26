"""Minimal SQL migration runner.

Usage:
    python -m app.db.migrate up            # apply all pending migrations
    python -m app.db.migrate down          # roll back the latest migration
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _versions() -> list[str]:
    return sorted(p.name.removesuffix(".up.sql") for p in MIGRATIONS_DIR.glob("*.up.sql"))


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT "
        "NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )


def _run_script(conn: sqlite3.Connection, sql: str, bookkeeping: str, version: str) -> None:
    # executescript() commits implicitly, so wrap everything in one explicit transaction.
    conn.executescript(f"BEGIN;\n{sql}\n;\n{bookkeeping.replace('?', repr(version))};\nCOMMIT;")


def migrate_up(conn: sqlite3.Connection) -> list[str]:
    _ensure_table(conn)
    applied = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
    done = []
    for version in _versions():
        if version in applied:
            continue
        sql = (MIGRATIONS_DIR / f"{version}.up.sql").read_text(encoding="utf-8")
        _run_script(conn, sql, "INSERT INTO schema_migrations(version) VALUES (?)", version)
        done.append(version)
    return done


def migrate_down(conn: sqlite3.Connection) -> str | None:
    _ensure_table(conn)
    row = conn.execute(
        "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    version = row[0]
    sql = (MIGRATIONS_DIR / f"{version}.down.sql").read_text(encoding="utf-8")
    _run_script(conn, sql, "DELETE FROM schema_migrations WHERE version = ?", version)
    return version


def main(argv: list[str]) -> int:
    from app.config import load_settings
    from app.repositories.sqlite import SqliteDatabase

    if len(argv) != 1 or argv[0] not in {"up", "down"}:
        print(__doc__)
        return 2
    db = SqliteDatabase(load_settings().database_path)
    conn = db.connect()
    try:
        if argv[0] == "up":
            print("applied:", migrate_up(conn) or "nothing")
        else:
            print("rolled back:", migrate_down(conn) or "nothing")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
