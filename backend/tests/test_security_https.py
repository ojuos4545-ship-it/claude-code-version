"""PRD 7 (transport encryption): HTTPS enforcement behind a TLS-terminating proxy,
HSTS, trusted proxy headers, and API docs disabled in production."""

from __future__ import annotations

import ipaddress

import pytest
from fastapi.testclient import TestClient

from app.config import ConfigError, load_settings
from app.main import create_app

PROXY = ("127.0.0.1", 40000)  # trusted by default in production
OUTSIDER = ("203.0.113.9", 40000)
HSTS = "max-age=31536000"


def prod_settings(tmp_path, **extra):
    env = {"APP_SECRET_KEY": "x" * 40, "APP_DATABASE_PATH": str(tmp_path / "p.db"), **extra}
    return load_settings(env)


@pytest.fixture
def prod_app(tmp_path, clock):
    return create_app(prod_settings(tmp_path), clock=clock)


def _client(app, peer, base_url="http://testserver"):
    return TestClient(app, client=peer, base_url=base_url)


def test_production_defaults():
    s = load_settings({"APP_SECRET_KEY": "x" * 40})
    assert s.require_https is True
    assert s.trusted_proxies == (
        ipaddress.ip_network("127.0.0.1/32"),
        ipaddress.ip_network("::1/128"),
    )
    assert s.rate_limit_enabled is True


@pytest.mark.parametrize("env", ["development", "test"])
def test_dev_defaults_do_not_enforce_or_trust(env):
    s = load_settings({"APP_ENV": env})
    assert s.require_https is False
    assert s.trusted_proxies == ()


def test_plain_http_from_proxy_is_refused(prod_app):
    with _client(prod_app, PROXY) as c:
        r = c.post("/v1/auth/anonymous", json={"privacy_consent": True})
        assert r.status_code == 403
        assert r.json()["error"]["code"] == "https_required"
        assert set(r.json()["error"]) == {"code", "message", "details"}
        r = c.get("/v1/me", headers={"X-Forwarded-Proto": "http"})
        assert r.status_code == 403


def test_https_via_trusted_proxy_passes_with_hsts(prod_app):
    with _client(prod_app, PROXY) as c:
        r = c.post(
            "/v1/auth/anonymous",
            json={"privacy_consent": True},
            headers={"X-Forwarded-Proto": "https"},
        )
        assert r.status_code == 201
        assert r.headers["strict-transport-security"] == HSTS
        # Error responses carry HSTS too.
        r = c.get("/v1/me", headers={"X-Forwarded-Proto": "https"})
        assert r.status_code == 401
        assert r.headers["strict-transport-security"] == HSTS


def test_forwarded_proto_from_untrusted_peer_is_ignored(prod_app):
    with _client(prod_app, OUTSIDER) as c:
        r = c.get("/v1/me", headers={"X-Forwarded-Proto": "https"})
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "https_required"


def test_direct_tls_is_accepted(prod_app):
    with _client(prod_app, OUTSIDER, base_url="https://testserver") as c:
        r = c.get("/v1/me")
    assert r.status_code == 401
    assert r.headers["strict-transport-security"] == HSTS


def test_healthz_allowed_over_http_for_load_balancers(prod_app):
    with _client(prod_app, OUTSIDER) as c:
        r = c.get("/healthz")
    assert r.status_code == 200
    assert "strict-transport-security" not in r.headers


def test_dev_mode_allows_http_without_hsts(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    r = client.post("/v1/auth/anonymous", json={"privacy_consent": True})
    assert r.status_code == 201
    assert "strict-transport-security" not in r.headers


def test_https_requirement_can_be_turned_off_and_on(tmp_path, clock):
    off = create_app(prod_settings(tmp_path, APP_REQUIRE_HTTPS="false"), clock=clock)
    with _client(off, OUTSIDER) as c:
        r = c.get("/v1/me")
    assert r.status_code == 401
    assert "strict-transport-security" not in r.headers

    on = create_app(
        load_settings(
            {
                "APP_ENV": "test",
                "APP_DATABASE_PATH": str(tmp_path / "t.db"),
                "APP_REQUIRE_HTTPS": "1",
                "APP_HSTS_MAX_AGE": "600",
            }
        ),
        clock=clock,
    )
    with _client(on, OUTSIDER) as c:
        assert c.get("/v1/me").status_code == 403
    with _client(on, OUTSIDER, base_url="https://testserver") as c:
        assert c.get("/v1/me").headers["strict-transport-security"] == "max-age=600"


def test_custom_trusted_proxy_network(tmp_path, clock):
    app = create_app(prod_settings(tmp_path, APP_TRUSTED_PROXIES="10.0.0.0/8"), clock=clock)
    with _client(app, ("10.1.2.3", 1)) as c:
        assert c.get("/v1/me", headers={"X-Forwarded-Proto": "https"}).status_code == 401
    # Loopback is no longer trusted once the list is set explicitly.
    with _client(app, PROXY) as c:
        assert c.get("/v1/me", headers={"X-Forwarded-Proto": "https"}).status_code == 403


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("APP_REQUIRE_HTTPS", "maybe"),
        ("APP_RATE_LIMIT_ENABLED", "sometimes"),
        ("APP_TRUSTED_PROXIES", "*"),
        ("APP_TRUSTED_PROXIES", "0.0.0.0/0"),
        ("APP_TRUSTED_PROXIES", "::/0"),
        ("APP_TRUSTED_PROXIES", "proxy.internal"),
        ("APP_HSTS_MAX_AGE", "-1"),
        ("APP_MAX_CONCURRENT_HASHES", "0"),
    ],
)
def test_invalid_security_settings_are_rejected(name, value):
    with pytest.raises(ConfigError):
        load_settings({"APP_SECRET_KEY": "x" * 40, name: value})


# ---- API docs ----------------------------------------------------------------
DOC_PATHS = ["/docs", "/redoc", "/openapi.json"]


def test_api_docs_disabled_in_production(prod_app):
    with _client(prod_app, OUTSIDER, base_url="https://testserver") as c:
        for path in DOC_PATHS:
            r = c.get(path)
            assert r.status_code == 404, path
            assert r.json()["error"]["code"] == "not_found"


def test_api_docs_available_in_development(client):
    for path in DOC_PATHS:
        assert client.get(path).status_code == 200, path
