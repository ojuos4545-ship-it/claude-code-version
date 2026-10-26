"""Settings read from environment variables.

Secrets never have a hard-coded value outside development/test mode.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

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

    return Settings(
        env=env,
        secret_key=secret_key,
        database_path=env_vars.get("APP_DATABASE_PATH", "data/app.db"),
        token_ttl_seconds=ttl,
        default_timezone=env_vars.get("APP_DEFAULT_TIMEZONE", "Asia/Seoul"),
        cors_origins=cors_origins,
    )


def _parse_origins(raw: str) -> tuple[str, ...]:
    """Comma-separated exact origins like "https://app.example.com". No wildcard."""
    origins = tuple(o.strip().rstrip("/") for o in raw.split(",") if o.strip())
    for origin in origins:
        if not _ORIGIN.match(origin):
            raise ConfigError(
                f"APP_CORS_ORIGINS entry {origin!r} must be scheme://host[:port] (no '*', no path)"
            )
    return origins
