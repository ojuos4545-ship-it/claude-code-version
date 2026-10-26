"""Auth endpoint rate limits (per IP, plus per email for login) and the argon2
concurrency cap. Counters are per process (see app/api/ratelimit.py)."""

from __future__ import annotations

import threading
import time

import pytest
from fastapi.testclient import TestClient

from app.api.ratelimit import AuthRateLimits, RateLimiter, Rule
from app.config import load_settings
from app.errors import ServerBusy
from app.main import create_app
from app.services.auth import HashGate
from tests.conftest import signup


class FakeTime:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def small_limits(app, time_fn=None, **rules):
    base = {
        "login_ip": Rule(100, 60),
        "login_email": Rule(100, 60),
        "signup_ip": Rule(100, 60),
        "anonymous_ip": Rule(100, 60),
        "link_ip": Rule(100, 60),
    }
    base.update({k: Rule(v, 60) for k, v in rules.items()})
    app.state.auth_limits = AuthRateLimits(base, time_fn=time_fn or FakeTime())
    return app.state.auth_limits


def assert_rate_limited(r):
    assert r.status_code == 429, r.text
    assert r.json()["error"]["code"] == "rate_limited"
    assert set(r.json()["error"]) == {"code", "message", "details"}
    assert int(r.headers["retry-after"]) >= 1


def _login(c, email="who@example.com", password="wrong-password", **kw):
    return c.post("/v1/auth/login", json={"email": email, "password": password}, **kw)


def test_login_limited_per_ip(app, client):
    small_limits(app, login_ip=3)
    for i in range(3):
        assert _login(client, email=f"u{i}@example.com").status_code == 401
    r = _login(client, email="other@example.com")
    assert_rate_limited(r)
    assert r.headers["retry-after"] == "60"


def test_login_limited_per_email_across_ips(tmp_path, clock):
    # Behind a trusted proxy each X-Forwarded-For address is its own IP bucket,
    # but the per-email limit still applies.
    settings = load_settings(
        {
            "APP_ENV": "test",
            "APP_DATABASE_PATH": str(tmp_path / "e.db"),
            "APP_TRUSTED_PROXIES": "127.0.0.1",
        }
    )
    app = create_app(settings, clock=clock)
    small_limits(app, login_email=2, login_ip=2)
    with TestClient(app, client=("127.0.0.1", 1)) as c:
        signup(c, "target@example.com", password="right-password")
        for i in range(2):
            fwd = {"X-Forwarded-For": f"198.51.100.{i}"}
            assert _login(c, "target@example.com", headers=fwd).status_code == 401
        r = _login(c, "Target@Example.com", headers={"X-Forwarded-For": "198.51.100.7"})
        assert_rate_limited(r)  # email is normalized before counting
        # Once limited, even the right password is refused until the window ends.
        r = _login(
            c, "target@example.com", "right-password", headers={"X-Forwarded-For": "198.51.100.8"}
        )
        assert_rate_limited(r)
        # Other accounts are unaffected.
        r = _login(c, "else@example.com", headers={"X-Forwarded-For": "198.51.100.9"})
        assert r.status_code == 401


def test_spoofed_forwarded_for_from_untrusted_peer_is_ignored(app, client):
    # Default test settings trust no proxy: the socket address is the key.
    small_limits(app, login_ip=2)
    for i in range(2):
        assert _login(client, headers={"X-Forwarded-For": f"192.0.2.{i}"}).status_code == 401
    assert_rate_limited(_login(client, headers={"X-Forwarded-For": "192.0.2.50"}))


def test_forwarded_for_uses_rightmost_untrusted_hop(tmp_path, clock):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "APP_DATABASE_PATH": str(tmp_path / "x.db"),
            "APP_TRUSTED_PROXIES": "127.0.0.1,10.0.0.0/8",
        }
    )
    app = create_app(settings, clock=clock)
    small_limits(app, login_ip=1)
    with TestClient(app, client=("127.0.0.1", 1)) as c:
        # Client-supplied left part changes, the real client (added by our proxy) does not.
        h1 = {"X-Forwarded-For": "1.1.1.1, 198.51.100.20, 10.0.0.2"}
        h2 = {"X-Forwarded-For": "2.2.2.2, 198.51.100.20, 10.0.0.2"}
        assert _login(c, headers=h1).status_code == 401
        assert_rate_limited(_login(c, headers=h2))
        assert _login(c, headers={"X-Forwarded-For": "198.51.100.21"}).status_code == 401


@pytest.mark.parametrize(
    ("rule", "path", "body"),
    [
        (
            "signup_ip",
            "/v1/auth/signup",
            {"email": "s@example.com", "password": "password-123", "privacy_consent": True},
        ),
        ("anonymous_ip", "/v1/auth/anonymous", {"privacy_consent": True}),
    ],
)
def test_signup_and_anonymous_limited_per_ip(app, client, rule, path, body):
    small_limits(app, **{rule: 1})
    assert client.post(path, json=body).status_code == 201
    assert_rate_limited(client.post(path, json=body))
    # Invalid requests count too (the limit runs before body validation).
    assert_rate_limited(client.post(path, json={}))


def test_link_limited_per_ip(app, client):
    small_limits(app, link_ip=1)
    token = client.post("/v1/auth/anonymous", json={"privacy_consent": True}).json()
    headers = {"Authorization": f"Bearer {token['access_token']}"}
    body = {"email": "bad", "password": "password-123"}
    assert client.post("/v1/auth/link", json=body, headers=headers).status_code == 422
    assert_rate_limited(client.post("/v1/auth/link", json=body, headers=headers))


def test_limit_resets_after_window(app, client):
    fake = FakeTime()
    small_limits(app, time_fn=fake, login_ip=1)
    assert _login(client).status_code == 401
    fake.now += 30
    r = _login(client)
    assert_rate_limited(r)
    assert r.headers["retry-after"] == "30"
    fake.now += 30
    assert _login(client).status_code == 401


def test_other_endpoints_not_limited(app, client, alice):
    small_limits(app, login_ip=0, signup_ip=0, anonymous_ip=0, link_ip=0)
    for _ in range(5):
        assert client.get("/v1/me", headers=alice).status_code == 200


def test_rate_limit_can_be_disabled(tmp_path, clock):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "APP_DATABASE_PATH": str(tmp_path / "d.db"),
            "APP_RATE_LIMIT_ENABLED": "false",
        }
    )
    app = create_app(settings, clock=clock)
    assert app.state.auth_limits is None
    with TestClient(app) as c:
        for _ in range(40):
            assert _login(c).status_code == 401


def test_default_limits_allow_normal_use(client):
    for _ in range(10):
        assert _login(client).status_code == 401
    assert_rate_limited(_login(client))  # 11th attempt on one email in 15 minutes


# ---- limiter memory bound --------------------------------------------------
def test_limiter_memory_is_bounded():
    fake = FakeTime()
    limiter = RateLimiter(Rule(5, 60), max_keys=100, time_fn=fake)
    for i in range(10_000):
        limiter.hit(f"10.0.{i // 256}.{i % 256}")
        fake.now += 0.001
    assert len(limiter) == 100


def test_limiter_evicts_expired_before_active():
    fake = FakeTime()
    limiter = RateLimiter(Rule(1, 60), max_keys=3, time_fn=fake)
    limiter.hit("old-1")
    limiter.hit("old-2")
    fake.now += 50
    limiter.hit("active")
    limiter.hit("active")  # over the limit
    fake.now += 15  # old-* expired, "active" still in its window
    limiter.hit("new-1")
    limiter.hit("new-2")
    assert limiter.hit("active") is not None  # still limited: not evicted


# ---- argon2 concurrency cap --------------------------------------------------
def test_hash_gate_caps_concurrency():
    gate = HashGate(2, wait_seconds=5)
    active = peak = 0
    lock = threading.Lock()

    def work():
        nonlocal active, peak
        with gate.slot():
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.05)
            with lock:
                active -= 1

    threads = [threading.Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert peak == 2


def test_login_returns_503_when_hash_slots_are_exhausted(app, client):
    app.state.hash_gate = HashGate(1, wait_seconds=0.05)
    with app.state.hash_gate.slot():  # another request is hashing
        r = _login(client)
        assert r.status_code == 503
        assert r.json()["error"]["code"] == "server_busy"
        assert r.headers["retry-after"] == "1"
        r = client.post(
            "/v1/auth/signup",
            json={"email": "b@example.com", "password": "password-123", "privacy_consent": True},
        )
        assert r.status_code == 503
    assert _login(client).status_code == 401  # slot released


def test_max_concurrent_hashes_setting(tmp_path, clock):
    settings = load_settings(
        {
            "APP_ENV": "test",
            "APP_DATABASE_PATH": str(tmp_path / "h.db"),
            "APP_MAX_CONCURRENT_HASHES": "2",
        }
    )
    assert settings.max_concurrent_hashes == 2
    gate = create_app(settings, clock=clock).state.hash_gate
    with gate.slot(), gate.slot():
        gate.wait_seconds = 0.01
        with pytest.raises(ServerBusy), gate.slot():
            pass
