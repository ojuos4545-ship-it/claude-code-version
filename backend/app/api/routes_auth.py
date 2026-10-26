from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import bearer_token, current_user, get_auth_service
from app.api.schemas import (
    DeleteAccountRequest,
    LoginRequest,
    SignupRequest,
    TokenOut,
    UpdateMeRequest,
    UserOut,
)
from app.domain.models import User
from app.services.auth import AuthService, IssuedToken

router = APIRouter(prefix="/v1")


def _token_out(t: IssuedToken, email: str) -> TokenOut:
    return TokenOut(access_token=t.token, expires_at=t.expires_at, user=UserOut.of(t.user, email))


@router.post("/auth/signup", status_code=status.HTTP_201_CREATED, response_model=TokenOut)
def signup(body: SignupRequest, request: Request, auth: AuthService = Depends(get_auth_service)):
    tz = body.timezone or request.app.state.settings.default_timezone
    return _token_out(auth.signup_with_password(body.email, body.password, tz), body.email)


@router.post("/auth/login", response_model=TokenOut)
def login(body: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    return _token_out(auth.login_with_password(body.email, body.password), body.email)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    _: User = Depends(current_user),
    auth: AuthService = Depends(get_auth_service),
):
    auth.logout(bearer_token(request) or "")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user), auth: AuthService = Depends(get_auth_service)):
    p = auth.profile(user)
    return UserOut.of(p.user, p.email)


@router.patch("/me", response_model=UserOut)
def update_me(
    body: UpdateMeRequest,
    user: User = Depends(current_user),
    auth: AuthService = Depends(get_auth_service),
):
    p = auth.profile(auth.update_timezone(user, body.timezone))
    return UserOut.of(p.user, p.email)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    body: DeleteAccountRequest,
    user: User = Depends(current_user),
    auth: AuthService = Depends(get_auth_service),
):
    auth.delete_account(user, body.password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
