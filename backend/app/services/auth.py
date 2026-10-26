"""Authentication.

Two independent parts:
- Sessions: opaque bearer tokens bound to a user id. Works the same no matter how
  the user logged in, and is sent in the Authorization header (no cookies), so web
  and mobile clients use it identically.
- Login methods: rows in auth_identities linked to a user. Only email + password
  ("password" provider) exists now. An anonymous start creates a user with no
  identity and issues a session; linking an account later adds an identity row.

Sessions slide: a token used after half its lifetime gets a fresh full lifetime. An
anonymous user has no other way back in, so a fixed expiry would lose their data.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.clock import Clock, is_valid_timezone, to_iso
from app.domain.models import PASSWORD_PROVIDER, AuthIdentity, User
from app.errors import (
    Conflict,
    Forbidden,
    InvalidCredentials,
    ServerBusy,
    Unauthenticated,
    ValidationFailed,
)
from app.repositories.base import DuplicateError, Repository

_hasher = PasswordHasher()
# Verified against when the email is unknown, so login timing does not reveal accounts.
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


class HashGate:
    """Caps concurrent argon2 hash/verify calls in this process.

    Each call allocates ~64 MiB (argon2-cffi default memory_cost), so a burst of
    password requests could otherwise exhaust memory. A request that cannot get a
    slot within `wait_seconds` fails with 503 instead of queueing, so waiting
    requests do not tie up the worker threads that every other endpoint needs.
    """

    def __init__(self, max_concurrent: int, wait_seconds: float = 3.0):
        self._slots = threading.BoundedSemaphore(max_concurrent)
        self.wait_seconds = wait_seconds

    @contextmanager
    def slot(self) -> Iterator[None]:
        if not self._slots.acquire(timeout=self.wait_seconds):
            raise ServerBusy()
        try:
            yield
        finally:
            self._slots.release()


_DEFAULT_GATE = HashGate(4)


@dataclass(frozen=True)
class IssuedToken:
    token: str
    expires_at: str
    user: User


@dataclass(frozen=True)
class Profile:
    user: User
    email: str | None  # None for a user without the password login method


class AuthService:
    def __init__(
        self,
        repo: Repository,
        clock: Clock,
        secret_key: str,
        token_ttl_seconds: int,
        hash_gate: HashGate = _DEFAULT_GATE,
    ):
        self.repo = repo
        self.clock = clock
        self._secret = secret_key.encode()
        self.ttl = timedelta(seconds=token_ttl_seconds)
        self._gate = hash_gate

    # ---- password hashing (memory-heavy: always through the gate) -------------
    def _hash(self, password: str) -> str:
        with self._gate.slot():
            return _hasher.hash(password)

    def _verify(self, password_hash: str | None, password: str) -> bool:
        """Always runs one argon2 verification, even without a hash, to keep timing equal."""
        with self._gate.slot():
            try:
                ok = _hasher.verify(password_hash or _DUMMY_HASH, password)
            except (VerificationError, InvalidHashError):
                return False
        return ok and password_hash is not None

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
        now = self.clock()
        token_hash = self._token_hash(token)
        found = self.repo.get_session(token_hash, to_iso(now))
        if found is None:
            raise Unauthenticated("Token is invalid or expired.")
        user, expires_at = found
        # Write only once the token is past half its lifetime, not on every request.
        if expires_at < to_iso(now + self.ttl / 2):
            self.repo.extend_session(token_hash, to_iso(now + self.ttl))
        return user

    def logout(self, token: str) -> None:
        self.repo.delete_session(self._token_hash(token))

    # ---- users ---------------------------------------------------------------
    def _new_user(self, timezone: str) -> User:
        if not is_valid_timezone(timezone):
            raise ValidationFailed.field("timezone", "invalid", "unknown IANA time zone")
        user = User(id=uuid.uuid4().hex, timezone=timezone, created_at=to_iso(self.clock()))
        # Every creation path requires the privacy consent, so consent time = creation time.
        self.repo.insert_user(user, consented_at=user.created_at)
        return user

    def start_anonymous(self, timezone: str) -> IssuedToken:
        """A user with no login method: start logging right away, link an account later."""
        with self.repo.transaction():
            return self.issue_session(self._new_user(timezone))

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
        password_hash = self._hash(password)
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

    def link_password(self, user: User, email: str, password: str) -> None:
        """Add email + password to a user who has no login method yet."""
        if self.repo.get_user_identity(user.id, PASSWORD_PROVIDER) is not None:
            raise Conflict("An email login is already linked to this account.")
        identity = AuthIdentity(PASSWORD_PROVIDER, email, user.id, self._hash(password))
        try:
            with self.repo.transaction():
                self.repo.insert_identity(identity, to_iso(self.clock()))
        except DuplicateError as exc:
            raise Conflict("Email is already registered.") from exc

    def login_with_password(self, email: str, password: str) -> IssuedToken:
        identity = self.repo.get_identity(PASSWORD_PROVIDER, email)
        if (
            not self._verify(identity.secret_hash if identity else None, password)
            or identity is None
        ):
            raise InvalidCredentials()
        user = self.repo.get_user(identity.user_id)
        if user is None:
            raise InvalidCredentials()
        self.repo.delete_expired_sessions(to_iso(self.clock()))
        return self.issue_session(user)

    # ---- account deletion (FR-6) --------------------------------------------
    def delete_account(self, user: User, password: str | None) -> None:
        """Delete sessions, login methods, all meals and the user in one transaction.

        A user with a password must confirm it. An anonymous user has no other
        credential, so holding the token is the only check possible.
        """
        identity = self.repo.get_user_identity(user.id, PASSWORD_PROVIDER)
        if identity is not None and not self._verify(identity.secret_hash, password or ""):
            raise Forbidden("Password confirmation failed.")
        with self.repo.transaction():
            self.repo.delete_sessions_for_user(user.id)
            self.repo.delete_meals_for_user(user.id)
            self.repo.delete_identities_for_user(user.id)
            self.repo.delete_user(user.id)
