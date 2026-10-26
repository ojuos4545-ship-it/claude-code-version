"""Settings read from environment variables.

Secrets never have a hard-coded value outside development/test mode.
"""

from __future__ import annotations

import ipaddress
import os
import re
from dataclasses import dataclass

IPNetwork = ipaddress.IPv4Network | ipaddress.IPv6Network

DEV_ENVS = {"development", "test"}
# Used only when APP_ENV is development or test. Never valid in production.
_DEV_SECRET_KEY = "dev-only-insecure-secret-key-change-me-0123456789"  # noqa: S105
MIN_SECRET_LENGTH = 32
# Browser origins allowed by CORS when APP_CORS_ORIGINS is unset in development/test.
_DEV_CORS_ORIGINS = (
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
)
# Proxies whose X-Forwarded-* headers are believed in production when
# APP_TRUSTED_PROXIES is unset: only a proxy on the same host. Anything wider must be
# set explicitly, because a trusted peer can claim any client IP and scheme.
_PROD_TRUSTED_PROXIES = ("127.0.0.1/32", "::1/128")
_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}
_ORIGIN = re.compile(r"^https?://[A-Za-z0-9.-]+(:\d{1,5})?$")


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    env: str
    secret_key: str
    database_path: str
    token_ttl_seconds: int
    default_timezone: str
    cors_origins: tuple[str, ...]
    # Reject plain-HTTP requests and send HSTS. Production default: on.
    require_https: bool = False
    hsts_max_age: int = 31_536_000
    # Peers (the TLS-terminating proxy) whose X-Forwarded-Proto/-For are believed.
    trusted_proxies: tuple[IPNetwork, ...] = ()
    rate_limit_enabled: bool = True
    # Concurrent argon2 hash/verify operations per process (each uses ~64 MiB).
    max_concurrent_hashes: int = 4

    @property
    def is_dev(self) -> bool:
        return self.env in DEV_ENVS


def load_settings(environ: dict[str, str] | None = None) -> Settings:
    env_vars = os.environ if environ is None else environ
    env = env_vars.get("APP_ENV", "production").strip().lower()

    secret_key = env_vars.get("APP_SECRET_KEY", "")
    if not secret_key:
        if env not in DEV_ENVS:
            raise ConfigError("APP_SECRET_KEY is required when APP_ENV is not development/test")
        secret_key = _DEV_SECRET_KEY
    if len(secret_key) < MIN_SECRET_LENGTH:
        raise ConfigError(f"APP_SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters")

    try:
        ttl = int(env_vars.get("APP_TOKEN_TTL_SECONDS", str(30 * 24 * 3600)))
    except ValueError as exc:
        raise ConfigError("APP_TOKEN_TTL_SECONDS must be an integer") from exc
    if ttl <= 0:
        raise ConfigError("APP_TOKEN_TTL_SECONDS must be positive")

    raw_origins = env_vars.get("APP_CORS_ORIGINS")
    if raw_origins is None:
        cors_origins = _DEV_CORS_ORIGINS if env in DEV_ENVS else ()
    else:
        cors_origins = _parse_origins(raw_origins)

    is_dev = env in DEV_ENVS
    require_https = _parse_bool(env_vars, "APP_REQUIRE_HTTPS", default=not is_dev)
    hsts_max_age = _parse_int(env_vars, "APP_HSTS_MAX_AGE", 31_536_000, minimum=0)
    raw_proxies = env_vars.get("APP_TRUSTED_PROXIES")
    if raw_proxies is None:
        trusted_proxies = () if is_dev else _parse_networks(",".join(_PROD_TRUSTED_PROXIES))
    else:
        trusted_proxies = _parse_networks(raw_proxies)

    return Settings(
        env=env,
        secret_key=secret_key,
        database_path=env_vars.get("APP_DATABASE_PATH", "data/app.db"),
        token_ttl_seconds=ttl,
        default_timezone=env_vars.get("APP_DEFAULT_TIMEZONE", "Asia/Seoul"),
        cors_origins=cors_origins,
        require_https=require_https,
        hsts_max_age=hsts_max_age,
        trusted_proxies=trusted_proxies,
        rate_limit_enabled=_parse_bool(env_vars, "APP_RATE_LIMIT_ENABLED", default=True),
        max_concurrent_hashes=_parse_int(env_vars, "APP_MAX_CONCURRENT_HASHES", 4, minimum=1),
    )


def _parse_bool(env_vars, name: str, default: bool) -> bool:
    raw = env_vars.get(name)
    if raw is None or not raw.strip():
        return default
    value = raw.strip().lower()
    if value in _TRUE:
        return True
    if value in _FALSE:
        return False
    raise ConfigError(f"{name} must be true or false")


def _parse_int(env_vars, name: str, default: int, minimum: int) -> int:
    raw = env_vars.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if value < minimum:
        raise ConfigError(f"{name} must be at least {minimum}")
    return value


def _parse_networks(raw: str) -> tuple[IPNetwork, ...]:
    """Comma-separated IPs or CIDRs, e.g. "10.0.0.5,10.1.0.0/16". No wildcard."""
    networks = []
    for item in (i.strip() for i in raw.split(",")):
        if not item:
            continue
        try:
            network = ipaddress.ip_network(item, strict=False)
        except ValueError as exc:
            raise ConfigError(
                f"APP_TRUSTED_PROXIES entry {item!r} must be an IP address or CIDR"
            ) from exc
        if network.prefixlen == 0:
            # Trusting every peer lets any client forge its IP and scheme.
            raise ConfigError(f"APP_TRUSTED_PROXIES entry {item!r} would trust every address")
        networks.append(network)
    return tuple(networks)


def _parse_origins(raw: str) -> tuple[str, ...]:
    """Comma-separated exact origins like "https://app.example.com". No wildcard."""
    origins = tuple(o.strip().rstrip("/") for o in raw.split(",") if o.strip())
    for origin in origins:
        if not _ORIGIN.match(origin):
            raise ConfigError(
                f"APP_CORS_ORIGINS entry {origin!r} must be scheme://host[:port] (no '*', no path)"
            )
    return origins
