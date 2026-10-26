"""QA: error responses a browser client must be able to read through CORS.

Both tests reproduce gaps found in pre-release QA (2026-10-26) and fail on purpose
until the product code is fixed:
- 429/503 carry Retry-After, but CORS does not expose it, so a web page cannot read it.
- 403 https_required is produced outside the CORS middleware, so it has no
  Access-Control-Allow-Origin and the browser reports a network error instead.
"""

from fastapi.testclient import TestClient

from app.config import load_settings
from app.main import create_app

ORIGIN = "https://app.example.com"


def _client(tmp_path, clock, **extra):
    env = {
        "APP_ENV": "test",
        "APP_DATABASE_PATH": str(tmp_path / "qa.db"),
        "APP_CORS_ORIGINS": ORIGIN,
        **extra,
    }
    return TestClient(create_app(load_settings(env), clock=clock))


def test_retry_after_is_exposed_to_browsers_on_429(tmp_path, clock):
    with _client(tmp_path, clock) as c:
        body = {"privacy_consent": True}
        for _ in range(20):
            c.post("/v1/auth/anonymous", json=body, headers={"Origin": ORIGIN})
        r = c.post("/v1/auth/anonymous", json=body, headers={"Origin": ORIGIN})
    assert r.status_code == 429
    assert r.headers["access-control-allow-origin"] == ORIGIN
    exposed = [h.strip().lower() for h in r.headers["access-control-expose-headers"].split(",")]
    assert "retry-after" in exposed


def test_https_required_is_readable_by_allowed_origin(tmp_path, clock):
    with _client(tmp_path, clock, APP_REQUIRE_HTTPS="true") as c:
        r = c.post("/v1/auth/anonymous", json={"privacy_consent": True}, headers={"Origin": ORIGIN})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "https_required"
    assert r.headers.get("access-control-allow-origin") == ORIGIN
