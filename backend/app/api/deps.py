from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Request

from app.domain.models import User
from app.repositories.base import Repository
from app.repositories.sqlite import SqliteRepository
from app.services.auth import AuthService
from app.services.meals import MealService


def get_repo(request: Request) -> Iterator[Repository]:
    conn = request.app.state.db.connect()
    try:
        yield SqliteRepository(conn)
    finally:
        conn.close()


def get_auth_service(request: Request, repo: Repository = Depends(get_repo)) -> AuthService:
    s = request.app.state.settings
    state = request.app.state
    return AuthService(repo, state.clock, s.secret_key, s.token_ttl_seconds, state.hash_gate)


def get_meal_service(request: Request, repo: Repository = Depends(get_repo)) -> MealService:
    return MealService(repo, request.app.state.clock)


def bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def current_user(request: Request, auth: AuthService = Depends(get_auth_service)) -> User:
    return auth.authenticate(bearer_token(request))
