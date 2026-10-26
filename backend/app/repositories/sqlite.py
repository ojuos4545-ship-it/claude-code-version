"""SQLite implementation of the Repository protocol (stdlib sqlite3, no server)."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from app.domain.models import MEAL_TYPE_ORDER, AuthIdentity, Meal, User
from app.repositories.base import DUP_IDENTIFIER, DUP_USER_PROVIDER, DuplicateError

_MEAL_COLS = "id, user_id, description, meal_date, meal_type, portion, memo, created_at, updated_at"


class SqliteDatabase:
    """Creates configured connections. One connection per request."""

    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        # isolation_level=None: autocommit; transactions are opened explicitly.
        # check_same_thread=False: FastAPI may run a dependency and the endpoint on
        # different threadpool threads; the connection is still used by one request only.
        conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn


def _row_to_meal(row: sqlite3.Row) -> Meal:
    return Meal(
        id=row["id"],
        user_id=row["user_id"],
        description=row["description"],
        meal_date=date.fromisoformat(row["meal_date"]),
        meal_type=row["meal_type"],
        portion=row["portion"],
        memo=row["memo"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_user(row: sqlite3.Row) -> User:
    return User(id=row["id"], timezone=row["timezone"], created_at=row["created_at"])


class SqliteRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._in_tx = False

    @contextmanager
    def transaction(self) -> Iterator[None]:
        if self._in_tx:  # nested: join the outer transaction
            yield
            return
        self.conn.execute("BEGIN IMMEDIATE")
        self._in_tx = True
        try:
            yield
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        else:
            self.conn.execute("COMMIT")
        finally:
            self._in_tx = False

    # ---- users -----------------------------------------------------------
    def insert_user(self, user: User, consented_at: str) -> None:
        self.conn.execute(
            "INSERT INTO users (id, timezone, created_at, consented_at) VALUES (?, ?, ?, ?)",
            (user.id, user.timezone, user.created_at, consented_at),
        )

    def get_user(self, user_id: str) -> User | None:
        row = self.conn.execute(
            "SELECT id, timezone, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return None if row is None else _row_to_user(row)

    def update_user_timezone(self, user_id: str, timezone: str) -> None:
        self.conn.execute("UPDATE users SET timezone = ? WHERE id = ?", (timezone, user_id))

    def delete_user(self, user_id: str) -> None:
        self.conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    # ---- auth identities -------------------------------------------------
    def insert_identity(self, identity: AuthIdentity, created_at: str) -> None:
        try:
            self.conn.execute(
                "INSERT INTO auth_identities "
                "(provider, identifier, user_id, secret_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    identity.provider,
                    identity.identifier,
                    identity.user_id,
                    identity.secret_hash,
                    created_at,
                ),
            )
        except sqlite3.IntegrityError as exc:
            # "UNIQUE constraint failed: auth_identities.user_id, auth_identities.provider"
            what = DUP_USER_PROVIDER if "auth_identities.user_id" in str(exc) else DUP_IDENTIFIER
            raise DuplicateError(what) from exc

    def _identity(self, where: str, params: tuple) -> AuthIdentity | None:
        row = self.conn.execute(
            "SELECT provider, identifier, user_id, secret_hash FROM auth_identities "  # noqa: S608
            f"WHERE {where}",
            params,
        ).fetchone()
        return None if row is None else AuthIdentity(**dict(row))

    def get_identity(self, provider: str, identifier: str) -> AuthIdentity | None:
        return self._identity("provider = ? AND identifier = ?", (provider, identifier))

    def get_user_identity(self, user_id: str, provider: str) -> AuthIdentity | None:
        return self._identity("user_id = ? AND provider = ?", (user_id, provider))

    def delete_identities_for_user(self, user_id: str) -> None:
        self.conn.execute("DELETE FROM auth_identities WHERE user_id = ?", (user_id,))

    # ---- sessions --------------------------------------------------------
    def insert_session(
        self, token_hash: str, user_id: str, created_at: str, expires_at: str
    ) -> None:
        self.conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) "
            "VALUES (?, ?, ?, ?)",
            (token_hash, user_id, created_at, expires_at),
        )

    def get_session(self, token_hash: str, now: str) -> tuple[User, str] | None:
        row = self.conn.execute(
            "SELECT u.id, u.timezone, u.created_at, s.expires_at FROM sessions s "
            "JOIN users u ON u.id = s.user_id WHERE s.token_hash = ? AND s.expires_at > ?",
            (token_hash, now),
        ).fetchone()
        return None if row is None else (_row_to_user(row), row["expires_at"])

    def extend_session(self, token_hash: str, expires_at: str) -> None:
        self.conn.execute(
            "UPDATE sessions SET expires_at = ? WHERE token_hash = ?", (expires_at, token_hash)
        )

    def delete_session(self, token_hash: str) -> None:
        self.conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))

    def delete_sessions_for_user(self, user_id: str) -> None:
        self.conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))

    def delete_expired_sessions(self, now: str) -> None:
        self.conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))

    # ---- meals -----------------------------------------------------------
    def insert_meal(
        self, meal: Meal, idempotency_key: str | None, request_hash: str | None
    ) -> None:
        try:
            self.conn.execute(
                f"INSERT INTO meals ({_MEAL_COLS}, idempotency_key, request_hash) "  # noqa: S608
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    meal.id,
                    meal.user_id,
                    meal.description,
                    meal.meal_date.isoformat(),
                    meal.meal_type,
                    meal.portion,
                    meal.memo,
                    meal.created_at,
                    meal.updated_at,
                    idempotency_key,
                    request_hash,
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise DuplicateError("idempotency_key") from exc

    def get_meal_by_idempotency_key(self, user_id: str, key: str) -> tuple[Meal, str | None] | None:
        row = self.conn.execute(
            f"SELECT {_MEAL_COLS}, request_hash FROM meals "  # noqa: S608
            "WHERE user_id = ? AND idempotency_key = ?",
            (user_id, key),
        ).fetchone()
        return None if row is None else (_row_to_meal(row), row["request_hash"])

    def get_meal(self, user_id: str, meal_id: str) -> Meal | None:
        row = self.conn.execute(
            f"SELECT {_MEAL_COLS} FROM meals WHERE user_id = ? AND id = ?",  # noqa: S608
            (user_id, meal_id),
        ).fetchone()
        return None if row is None else _row_to_meal(row)

    def update_meal(self, meal: Meal) -> bool:
        cur = self.conn.execute(
            "UPDATE meals SET description = ?, meal_date = ?, meal_type = ?, portion = ?, "
            "memo = ?, updated_at = ? WHERE user_id = ? AND id = ?",
            (
                meal.description,
                meal.meal_date.isoformat(),
                meal.meal_type,
                meal.portion,
                meal.memo,
                meal.updated_at,
                meal.user_id,
                meal.id,
            ),
        )
        return cur.rowcount == 1

    def delete_meal(self, user_id: str, meal_id: str) -> bool:
        cur = self.conn.execute(
            "DELETE FROM meals WHERE user_id = ? AND id = ?", (user_id, meal_id)
        )
        return cur.rowcount == 1

    def delete_meals_for_user(self, user_id: str) -> None:
        self.conn.execute("DELETE FROM meals WHERE user_id = ?", (user_id,))

    def list_meals(
        self, user_id: str, start: date, end: date, limit: int, offset: int
    ) -> list[Meal]:
        # Sort: meal_date -> meal_type (breakfast, lunch, dinner, snack, none) -> created_at.
        case = "CASE meal_type " + " ".join("WHEN ? THEN ?" for _ in MEAL_TYPE_ORDER)
        case += f" ELSE {len(MEAL_TYPE_ORDER)} END"
        case_params: list[object] = []
        for i, value in enumerate(MEAL_TYPE_ORDER):
            case_params += [value, i]
        rows = self.conn.execute(
            f"SELECT {_MEAL_COLS} FROM meals "  # noqa: S608
            "WHERE user_id = ? AND meal_date BETWEEN ? AND ? "
            f"ORDER BY meal_date, {case}, created_at, id LIMIT ? OFFSET ?",
            (user_id, start.isoformat(), end.isoformat(), *case_params, limit, offset),
        ).fetchall()
        return [_row_to_meal(r) for r in rows]

    def recent_descriptions(self, user_id: str, since: str, limit: int) -> list[str]:
        rows = self.conn.execute(
            "SELECT description, MAX(created_at) AS last_used FROM meals "
            "WHERE user_id = ? AND created_at >= ? "
            "GROUP BY description ORDER BY last_used DESC, description LIMIT ?",
            (user_id, since, limit),
        ).fetchall()
        return [r["description"] for r in rows]

    def count_meals_by_date_and_portion(
        self, user_id: str, start: date, end: date
    ) -> list[tuple[date, str | None, int]]:
        rows = self.conn.execute(
            "SELECT meal_date, portion, COUNT(*) AS n FROM meals "
            "WHERE user_id = ? AND meal_date BETWEEN ? AND ? GROUP BY meal_date, portion",
            (user_id, start.isoformat(), end.isoformat()),
        ).fetchall()
        return [(date.fromisoformat(r["meal_date"]), r["portion"], r["n"]) for r in rows]
