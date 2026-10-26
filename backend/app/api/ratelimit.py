"""In-process request rate limits for the auth endpoints.

Fixed-window counters kept in this process's memory. They are NOT shared between
processes or instances: with N instances behind a load balancer a client gets up to
N times the limit. Move the counters to a shared store (e.g. Redis) before scaling out.

Memory is bounded: each limiter keeps at most `max_keys` keys. When full, expired
windows are dropped first, then the oldest windows (an attacker with that many
source addresses could reset someone else's counter, which beats unbounded growth).
"""

from __future__ import annotations

import math
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Request

from app.errors import RateLimited


@dataclass(frozen=True)
class Rule:
    limit: int
    window_seconds: float


# [assumption] No traffic data yet. Per-IP limits stay loose because many users can
# share one address (mobile carrier NAT, offices); the per-email login limit is the
# tight one against password guessing.
DEFAULT_RULES: dict[str, Rule] = {
    "login_ip": Rule(30, 600),
    "login_email": Rule(10, 900),
    "signup_ip": Rule(20, 600),
    "anonymous_ip": Rule(20, 600),
    "link_ip": Rule(10, 600),
}
DEFAULT_MAX_KEYS = 10_000


class RateLimiter:
    def __init__(
        self,
        rule: Rule,
        max_keys: int = DEFAULT_MAX_KEYS,
        time_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.rule = rule
        self.max_keys = max_keys
        self._time = time_fn
        self._lock = threading.Lock()  # sync endpoints run in a thread pool
        # key -> [window_start, count]; ordered by window_start (oldest first)
        self._windows: OrderedDict[str, list[float]] = OrderedDict()

    def __len__(self) -> int:
        return len(self._windows)

    def hit(self, key: str) -> float | None:
        """Count one request. Returns seconds until retry when over the limit, else None."""
        with self._lock:
            now = self._time()
            window = self._windows.get(key)
            if window is None or now - window[0] >= self.rule.window_seconds:
                if window is None and len(self._windows) >= self.max_keys:
                    self._evict(now)
                self._windows[key] = [now, 1]
                self._windows.move_to_end(key)
                return None
            window[1] += 1
            if window[1] > self.rule.limit:
                return self.rule.window_seconds - (now - window[0])
            return None

    def _evict(self, now: float) -> None:
        while self._windows:
            start, _ = next(iter(self._windows.values()))
            if now - start < self.rule.window_seconds:
                break
            self._windows.popitem(last=False)
        while len(self._windows) >= self.max_keys:
            self._windows.popitem(last=False)


class AuthRateLimits:
    """One limiter per rule name, shared by every request in this process."""

    def __init__(
        self,
        rules: dict[str, Rule] | None = None,
        max_keys: int = DEFAULT_MAX_KEYS,
        time_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limiters = {
            name: RateLimiter(rule, max_keys, time_fn)
            for name, rule in (rules or DEFAULT_RULES).items()
        }

    def enforce(self, name: str, key: str) -> None:
        retry_after = self.limiters[name].hit(key)
        if retry_after is not None:
            raise RateLimited(math.ceil(retry_after))


def client_ip(request: Request) -> str:
    # ProxyHttpsMiddleware already replaced the socket address with the
    # X-Forwarded-For client when (and only when) the peer is a trusted proxy.
    return request.client.host if request.client else "unknown"


def enforce(request: Request, name: str, key: str) -> None:
    limits: AuthRateLimits | None = request.app.state.auth_limits
    if limits is not None:
        limits.enforce(name, key)


def limit_by_ip(name: str) -> Callable[[Request], None]:
    """Dependency: runs before body validation, so invalid requests count too."""

    def dependency(request: Request) -> None:
        enforce(request, name, client_ip(request))

    return dependency
