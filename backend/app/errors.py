"""Domain errors. Each maps to one HTTP status and a stable error code."""

from __future__ import annotations


class AppError(Exception):
    status_code = 500
    code = "internal_error"
    default_message = "Internal server error."

    def __init__(self, message: str | None = None, details: list[dict] | None = None):
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.details = details or []


class ValidationFailed(AppError):
    status_code = 422
    code = "validation_error"
    default_message = "Request validation failed."

    @classmethod
    def field(cls, field: str, reason: str, message: str) -> ValidationFailed:
        return cls(details=[{"field": field, "reason": reason, "message": message}])


class Unauthenticated(AppError):
    status_code = 401
    code = "unauthenticated"
    default_message = "Authentication required."


class InvalidCredentials(AppError):
    status_code = 401
    code = "invalid_credentials"
    default_message = "Email or password is incorrect."


class Forbidden(AppError):
    status_code = 403
    code = "forbidden"
    default_message = "Not allowed."


class NotFound(AppError):
    status_code = 404
    code = "not_found"
    default_message = "Resource not found."


class Conflict(AppError):
    status_code = 409
    code = "conflict"
    default_message = "Conflict."
