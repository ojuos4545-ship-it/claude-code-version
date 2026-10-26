"""Browser (web client) access via CORS. Allowed origins come from APP_CORS_ORIGINS."""

import pytest
from fastapi.testclient import TestClient

from app.config import load_settings
from app.main import create_app


@pytest.fixture
def cors_client(tmp_path, clock):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "APP_DATABASE_PATH": str(tmp_path / "cors.db"),
            "APP_CORS_ORIGINS": "https://app.example.com",
        }
    )
    with TestClient(create_app(settings, clock=clock)) as c:
        yield c


def test_preflight_from_allowed_origin(cors_client):
    r = cors_client.options(
        "/v1/meals",
        headers={
            "Origin": "https://app.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type, idempotency-key",
        },
    )
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "https://app.example.com"
    allowed = r.headers["access-control-allow-headers"].lower()
    assert "authorization" in allowed and "idempotency-key" in allowed
    assert "access-control-allow-credentials" not in r.headers  # no cookies


def test_simple_request_from_allowed_origin(cors_client):
    r = cors_client.get("/healthz", headers={"Origin": "https://app.example.com"})
    assert r.headers["access-control-allow-origin"] == "https://app.example.com"
    assert "idempotent-replayed" in r.headers["access-control-expose-headers"].lower()


def test_disallowed_origin_gets_no_cors_headers(cors_client):
    r = cors_client.get("/healthz", headers={"Origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in r.headers
    pre = cors_client.options(
        "/v1/meals",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert pre.status_code == 400
    assert "access-control-allow-origin" not in pre.headers


def test_no_cors_when_no_origins_configured(tmp_path, clock):
    settings = load_settings(
        {"APP_SECRET_KEY": "x" * 40, "APP_DATABASE_PATH": str(tmp_path / "p.db")}
    )
    with TestClient(create_app(settings, clock=clock)) as c:
        r = c.get("/healthz", headers={"Origin": "http://localhost:3000"})
    assert "access-control-allow-origin" not in r.headers


def test_unhandled_500_is_readable_by_allowed_origin(tmp_path, clock):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "APP_DATABASE_PATH": str(tmp_path / "c500.db"),
            "APP_CORS_ORIGINS": "https://app.example.com",
        }
    )
    app = create_app(settings, clock=clock)

    @app.get("/crash")
    def crash():
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/crash", headers={"Origin": "https://app.example.com"})
    assert r.status_code == 500
    assert r.json()["error"]["code"] == "internal_error"
    assert r.headers["access-control-allow-origin"] == "https://app.example.com"


def test_preflight_passes_when_https_is_required_so_the_403_is_readable(tmp_path, clock):
    # A non-2xx preflight fails in the browser whatever its headers, so the preflight
    # is answered by CORS and the real request gets a 403 the page can read.
    settings = load_settings(
        {
            "APP_ENV": "test",
            "APP_DATABASE_PATH": str(tmp_path / "pre.db"),
            "APP_CORS_ORIGINS": "https://app.example.com",
            "APP_REQUIRE_HTTPS": "true",
        }
    )
    with TestClient(create_app(settings, clock=clock)) as c:
        pre = c.options(
            "/v1/meals",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization, content-type",
            },
        )
        assert pre.status_code == 200
        assert pre.headers["access-control-allow-origin"] == "https://app.example.com"
        r = c.post("/v1/meals", json={}, headers={"Origin": "https://app.example.com"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "https_required"
    assert r.headers["access-control-allow-origin"] == "https://app.example.com"
