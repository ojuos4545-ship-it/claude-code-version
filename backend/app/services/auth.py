"""Authentication.

Two independent parts:
- Sessions: opaque bearer tokens bound to a user id. Works the same no matter how
  the user logged in, and is sent in the Authorization header (no cookies), so web
  and mobile clients use it identically.
- Login methods: rows in auth_identities linked to a user. Only email + password
  ("password" provider) exists now. An anonymous start would create a user with no
  identity and issue a session; linking an account later adds an identity row.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.clock import Clock, is_valid_timezone, to_iso
from app.domain.models import PASSWORD_PROVIDER, AuthIdentity, User
from app.errors import Conflict, Forbidden, InvalidCredentials, Unauthenticated, ValidationFailed
from app.repositories.base import DuplicateError, Repository

_hasher = PasswordHasher()
# Verified against when the email is unknown, so login timing does not reveal accounts.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


@dataclass(frozen=True)
class IssuedToken:
    token: str
    expires_at: str
    user: User


@dataclass(frozen=True)
class Profile:
    user: User
    email: str | None  # None for a user without the password login method


def _verify(password_hash: str | None, password: str) -> bool:
    """Always runs one argon2 verification, even without a hash, to keep timing equal."""
    try:
        ok = _hasher.verify(password_hash or _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False
    return ok and password_hash is not None


class AuthService:
    def __init__(self, repo: Repository, clock: Clock, secret_key: str, token_ttl_seconds: int):
        self.repo = repo
        self.clock = clock
        self._secret = secret_key.encode()
        self.ttl = timedelta(seconds=token_ttl_seconds)

    # ---- sessions (login-method independent) -------------------------------
    def _token_hash(self, token: str) -> str:
        # Only an HMAC of the token is stored; a DB leak does not expose usable tokens.
        return hmac.new(self._secret, token.encode(), hashlib.sha256).hexdigest()

    def issue_session(self, user: User) -> IssuedToken:
        now = self.clock()
        token = secrets.token_urlsafe(32)
        expires_at = to_iso(now + self.ttl)
        self.repo.insert_session(self._token_hash(token), user.id, to_iso(now), expires_at)
        return IssuedToken(token=token, expires_at=expires_at, user=user)

    def authenticate(self, token: str | None) -> User:
        if not token:
            raise Unauthenticated()
        user = self.repo.get_session_user(self._token_hash(token), to_iso(self.clock()))
        if user is None:
            raise Unauthenticated("Token is invalid or expired.")
        return user

    def logout(self, token: str) -> None:
        self.repo.delete_session(self._token_hash(token))

    # ---- users ---------------------------------------------------------------
    def _new_user(self, timezone: str) -> User:
        if not is_valid_timezone(timezone):
            raise ValidationFailed.field("timezone", "invalid", "unknown IANA time zone")
        user = User(id=uuid.uuid4().hex, timezone=timezone, created_at=to_iso(self.clock()))
        self.repo.insert_user(user)
        return user

    def profile(self, user: User) -> Profile:
        identity = self.repo.get_user_identity(user.id, PASSWORD_PROVIDER)
        return Profile(user=user, email=identity.identifier if identity else None)

    def update_timezone(self, user: User, timezone: str) -> User:
        if not is_valid_timezone(timezone):
            raise ValidationFailed.field("timezone", "invalid", "unknown IANA time zone")
        self.repo.update_user_timezone(user.id, timezone)
        return User(id=user.id, timezone=timezone, created_at=user.created_at)

    # ---- password login method ----------------------------------------------
    def signup_with_password(self, email: str, password: str, timezone: str) -> IssuedToken:
        password_hash = _hasher.hash(password)
        try:
            with self.repo.transaction():
                user = self._new_user(timezone)
                self.repo.insert_identity(
                    AuthIdentity(PASSWORD_PROVIDER, email, user.id, password_hash),
                    user.created_at,
                )
                return self.issue_session(user)
        except DuplicateError as exc:
            raise Conflict("Email is already registered.") from exc

    def login_with_password(self, email: str, password: str) -> IssuedToken:
        identity = self.repo.get_identity(PASSWORD_PROVIDER, email)
        if not _verify(identity.secret_hash if identity else None, password) or identity is None:
            raise InvalidCredentials()
        user = self.repo.get_user(identity.user_id)
        if user is None:
            raise InvalidCredentials()
        self.repo.delete_expired_sessions(to_iso(self.clock()))
        return self.issue_session(user)

    # ---- account deletion (FR-6) --------------------------------------------
    def delete_account(self, user: User, password: str) -> None:
        """Delete sessions, login methods, all meals and the user in one transaction."""
        identity = self.repo.get_user_identity(user.id, PASSWORD_PROVIDER)
        # When identity-less (anonymous) users are added, decide their confirmation step.
        if not _verify(identity.secret_hash if identity else None, password):
            raise Forbidden("Password confirmation failed.")
        with self.repo.transaction():
            self.repo.delete_sessions_for_user(user.id)
            self.repo.delete_meals_for_user(user.id)
            self.repo.delete_identities_for_user(user.id)
            self.repo.delete_user(user.id)
