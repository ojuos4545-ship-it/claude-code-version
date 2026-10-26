"""Pure ASGI middleware: proxy headers + HTTPS enforcement, and the last-resort 500.

Both are plain ASGI (no BaseHTTPMiddleware) so they see every request, including
CORS preflights, and so the catch-all can swallow an exception instead of letting it
reach Starlette's ServerErrorMiddleware, which re-raises it to the server (uvicorn
then logs the traceback and the exception message, which may contain meal text).
"""

from __future__ import annotations

import ipaddress
import logging

from fastapi.responses import JSONResponse
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import IPNetwork

logger = logging.getLogger("easy_meal_log")

# Load balancers usually health-check the app directly over plain HTTP.
HTTPS_EXEMPT_PATHS = frozenset({"/healthz"})
_MAX_LOGGED_PATH = 200


def error_response(
    status: int,
    code: str,
    message: str,
    details: list | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": details or []}}
    return JSONResponse(status_code=status, content=body, headers=headers)


class CatchAllErrorsMiddleware:
    """Outermost handler: turns any unhandled exception into the standard 500 body.

    Logs only the exception type, method and path (no query string, body or message):
    PRD 7 forbids meal text, memos and secrets in logs.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        response_started = False

        async def send_wrapper(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            path = scope.get("path", "")[:_MAX_LOGGED_PATH]
            # %r escapes control characters, so a crafted path cannot forge log lines.
            logger.error("unhandled %s on %s %r", type(exc).__name__, scope.get("method"), path)
            if response_started:
                return  # Too late for a 500; the server closes the incomplete response.
            response = error_response(500, "internal_error", "Internal server error.")
            await response(scope, receive, send)


class ProxyHttpsMiddleware:
    """Applies X-Forwarded-Proto/-For from trusted proxies, then enforces HTTPS.

    Proxy headers are believed only when the socket peer is in `trusted_proxies`;
    otherwise any client could claim "https" or a fake IP (and dodge IP rate limits).
    The resolved scheme and client are written back to the scope, so the rest of
    the app reads them from `request.url.scheme` and `request.client.host`.

    With `require_https`, a plain-HTTP request is refused with 403 rather than
    redirected: the request (and its bearer token) already crossed the network in
    the clear, and redirecting a POST would silently resend its body.
    """

    def __init__(
        self,
        app: ASGIApp,
        trusted_proxies: tuple[IPNetwork, ...],
        require_https: bool,
        hsts_max_age: int,
    ) -> None:
        self.app = app
        self.trusted_proxies = trusted_proxies
        self.require_https = require_https
        self.hsts = f"max-age={hsts_max_age}"

    def _is_trusted(self, host: str | None) -> bool:
        if not host or not self.trusted_proxies:
            return False
        try:
            addr = ipaddress.ip_address(host)
        except ValueError:
            return False
        return any(addr in net for net in self.trusted_proxies)

    def _client_from_forwarded_for(self, values: list[str]) -> str | None:
        # Each proxy appends the address it received from, so walk from the right and
        # stop at the first hop that is not one of our proxies: that is the client.
        # Entries further left are whatever the client sent and cannot be believed.
        hops = [h.strip() for v in values for h in v.split(",") if h.strip()]
        for hop in reversed(hops):
            if not self._is_trusted(hop):
                try:
                    return str(ipaddress.ip_address(hop))
                except ValueError:
                    return None  # malformed: fall back to the socket address
        return hops[0] if hops else None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        if self._is_trusted(client[0] if client else None):
            headers = Headers(scope=scope)
            scope = dict(scope)
            proto = headers.get("x-forwarded-proto")
            if proto:
                # The proxy next to the app must set (not append) the original scheme.
                scope["scheme"] = proto.split(",")[-1].strip().lower()
            forwarded_host = self._client_from_forwarded_for(headers.getlist("x-forwarded-for"))
            if forwarded_host:
                scope["client"] = (forwarded_host, 0)

        if not self.require_https or scope["path"] in HTTPS_EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return

        if scope["scheme"] != "https":
            response = error_response(403, "https_required", "HTTPS is required.")
            await response(scope, receive, send)
            return

        async def send_with_hsts(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["Strict-Transport-Security"] = self.hsts
            await send(message)

        await self.app(scope, receive, send_with_hsts)
