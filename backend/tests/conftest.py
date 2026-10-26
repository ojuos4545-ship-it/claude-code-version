from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import load_settings
from app.main import create_app


class FakeClock:
    """Controllable UTC clock. Each call advances 1ms so timestamps stay ordered."""

    def __init__(self, start: datetime):
        self.now = start
        self._tick = itertools.count()

    def __call__(self) -> datetime:
        return self.now + timedelta(milliseconds=next(self._tick))

    def set(self, value: datetime) -> None:
        self.now = value

    def advance(self, **kwargs) -> None:
        self.now += timedelta(**kwargs)


# 2026-10-26 12:00 UTC == 2026-10-26 21:00 in Asia/Seoul
DEFAULT_NOW = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(DEFAULT_NOW)


@pytest.fixture
def settings(tmp_path):
    return load_settings({"APP_ENV": "test", "APP_DATABASE_PATH": str(tmp_path / "test.db")})


@pytest.fixture
def app(settings, clock):
    return create_app(settings, clock=clock)


@pytest.fixture
def client(app):
    # raise_server_exceptions=False: assert on the real 500 response instead.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


_counter = itertools.count()


def signup(client, email: str | None = None, password: str = "correct-horse-1", **extra):
    email = email or f"user{next(_counter)}@example.com"
    body = {"email": email, "password": password, "privacy_consent": True, **extra}
    r = client.post("/v1/auth/signup", json=body)
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def alice(client):
    return signup(client, "alice@example.com")


@pytest.fixture
def bob(client):
    return signup(client, "bob@example.com")


def create_meal(client, headers, **body):
    body.setdefault("description", "kimchi stew")
    r = client.post("/v1/meals", json=body, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()
