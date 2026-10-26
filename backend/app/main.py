"""App factory and consistent error responses.

Error body format (every non-2xx response):
    {"error": {"code": str, "message": str, "details": [{"field", "reason", "message"}]}}

Middleware, outermost first:
    CatchAllErrorsMiddleware (last resort, for a failure inside the CORS layer itself)
    -> CORS (so every response below, including errors, carries CORS headers)
    -> CatchAllErrorsMiddleware (unhandled exception -> 500, never re-raised)
    -> ProxyHttpsMiddleware (trusted proxy headers, HTTPS 403 + HSTS)
    -> routes.
CORS sits outside the HTTPS check and the 500 handler so a browser can read those
error bodies; otherwise it reports a bare network error. A CORS preflight is answered
by the CORS layer before the HTTPS check: a non-2xx preflight fails in the browser no
matter what headers it has, and the real request is still refused with a readable 403.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import routes_auth, routes_meals
from app.api.middleware import CatchAllErrorsMiddleware, ProxyHttpsMiddleware
from app.api.middleware import error_response as _error
from app.api.ratelimit import AuthRateLimits
from app.clock import Clock, system_clock
from app.config import Settings, load_settings
from app.db.migrate import migrate_up
from app.errors import AppError
from app.repositories.sqlite import SqliteDatabase
from app.services.auth import HashGate

_HTTP_CODES = {401: "unauthenticated", 404: "not_found", 405: "method_not_allowed"}


def _field_name(loc: tuple) -> str:
    # ("body", "description") -> "description"; ("query", "limit") -> "limit"
    parts = [str(p) for p in loc if p not in ("body", "query", "header", "path")]
    return ".".join(parts) or "body"


def create_app(settings: Settings | None = None, clock: Clock = system_clock) -> FastAPI:
    settings = settings or load_settings()
    # API docs only in development/test: in production they map the attack surface.
    docs = settings.is_dev
    app = FastAPI(
        title="Easy Meal Log API",
        version="0.1.0",
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.state.settings = settings
    app.state.clock = clock
    # Process-wide: shared by all requests (and threads) of this process only.
    app.state.auth_limits = AuthRateLimits() if settings.rate_limit_enabled else None
    app.state.hash_gate = HashGate(settings.max_concurrent_hashes)
    app.state.db = SqliteDatabase(settings.database_path)

    conn = app.state.db.connect()
    try:
        migrate_up(conn)
    finally:
        conn.close()

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else {}
        if exc.retry_after is not None:
            headers["Retry-After"] = str(exc.retry_after)
        return _error(exc.status_code, exc.code, exc.message, exc.details, headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        details = [
            {
                "field": _field_name(tuple(e.get("loc", ()))),
                "reason": e.get("type", "invalid"),
                "message": str(e.get("msg", "invalid value")),
            }
            for e in exc.errors()
        ]
        return _error(422, "validation_error", "Request validation failed.", details)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException):
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        return _error(exc.status_code, code, str(exc.detail) if exc.status_code < 500 else "Error")

    # No exception_handler(Exception): Starlette's ServerErrorMiddleware would run it
    # and then re-raise to uvicorn, which logs the full traceback and message.
    # CatchAllErrorsMiddleware handles it instead (see the middleware order above).

    # Added innermost first: each add_middleware wraps everything added before it.
    app.add_middleware(
        ProxyHttpsMiddleware,
        trusted_proxies=settings.trusted_proxies,
        require_https=settings.require_https,
        hsts_max_age=settings.hsts_max_age,
    )
    app.add_middleware(CatchAllErrorsMiddleware)

    # Auth is a bearer token in the Authorization header (no cookies), so credentials
    # mode stays off. Mobile apps do not use CORS at all.
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
            # Retry-After: 429/503 tell the client how long to wait.
            expose_headers=["Idempotent-Replayed", "Retry-After"],
            max_age=600,
        )
        app.add_middleware(CatchAllErrorsMiddleware)

    app.include_router(routes_auth.router)
    app.include_router(routes_meals.router)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"status": "ok"}

    return app
