"""App factory and consistent error responses.

Error body format (every non-2xx response):
    {"error": {"code": str, "message": str, "details": [{"field", "reason", "message"}]}}
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import routes_auth, routes_meals
from app.clock import Clock, system_clock
from app.config import Settings, load_settings
from app.db.migrate import migrate_up
from app.errors import AppError
from app.repositories.sqlite import SqliteDatabase

logger = logging.getLogger("easy_meal_log")

_HTTP_CODES = {401: "unauthenticated", 404: "not_found", 405: "method_not_allowed"}


def _error(status: int, code: str, message: str, details: list | None = None, headers=None):
    body = {"error": {"code": code, "message": message, "details": details or []}}
    return JSONResponse(status_code=status, content=body, headers=headers)


def _field_name(loc: tuple) -> str:
    # ("body", "description") -> "description"; ("query", "limit") -> "limit"
    parts = [str(p) for p in loc if p not in ("body", "query", "header", "path")]
    return ".".join(parts) or "body"


def create_app(settings: Settings | None = None, clock: Clock = system_clock) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Easy Meal Log API", version="0.1.0")
    app.state.settings = settings
    app.state.clock = clock
    app.state.db = SqliteDatabase(settings.database_path)

    conn = app.state.db.connect()
    try:
        migrate_up(conn)
    finally:
        conn.close()

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
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

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # Log type and path only: no request body (meal text, passwords) in logs.
        logger.error("unhandled %s on %s %s", type(exc).__name__, request.method, request.url.path)
        return _error(500, "internal_error", "Internal server error.")

    # Auth is a bearer token in the Authorization header (no cookies), so credentials
    # mode stays off. Mobile apps do not use CORS at all.
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
            expose_headers=["Idempotent-Replayed"],
            max_age=600,
        )

    app.include_router(routes_auth.router)
    app.include_router(routes_meals.router)

    @app.get("/healthz", include_in_schema=False)
    def healthz():
        return {"status": "ok"}

    return app
