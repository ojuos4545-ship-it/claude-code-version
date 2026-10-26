"""Request/response models. Unknown fields are rejected (extra="forbid") so values
like calories or grams are never silently stored."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator, model_validator

from app.domain.models import Meal, MealType, Portion, User
from app.domain.rules import normalize_description, normalize_memo

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_iso_date(value: object) -> object:
    """Accept only "YYYY-MM-DD" strings (no timestamps, no datetimes)."""
    if value is None or isinstance(value, date):
        return value
    if not isinstance(value, str) or not _ISO_DATE.match(value):
        raise ValueError("must be a date string in YYYY-MM-DD format")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("is not a valid calendar date") from None


StrictDate = Annotated[date, BeforeValidator(_parse_iso_date)]
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN, PASSWORD_MAX = 8, 128  # [assumption]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---- auth ------------------------------------------------------------------
class SignupRequest(_Strict):
    email: str = Field(max_length=254)
    password: str = Field(min_length=PASSWORD_MIN, max_length=PASSWORD_MAX)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if not _EMAIL.match(v):
            raise ValueError("must be a valid email address")
        return v


class LoginRequest(_Strict):
    email: str = Field(max_length=254)
    password: str = Field(max_length=PASSWORD_MAX)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        return v.strip().lower()


class UpdateMeRequest(_Strict):
    timezone: str = Field(max_length=64)


class DeleteAccountRequest(_Strict):
    password: str = Field(max_length=PASSWORD_MAX)


class UserOut(BaseModel):
    id: str
    email: str | None  # null for a user without the email/password login method
    timezone: str
    created_at: str

    @classmethod
    def of(cls, u: User, email: str | None) -> UserOut:
        return cls(id=u.id, email=email, timezone=u.timezone, created_at=u.created_at)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_at: str
    user: UserOut


# ---- meals -----------------------------------------------------------------
class MealCreateRequest(_Strict):
    description: str
    meal_date: StrictDate | None = None
    meal_type: MealType | None = None
    portion: Portion | None = None
    memo: str | None = None

    @field_validator("description")
    @classmethod
    def _desc(cls, v: str) -> str:
        return normalize_description(v)

    @field_validator("memo")
    @classmethod
    def _memo(cls, v: str | None) -> str | None:
        return normalize_memo(v)


class MealUpdateRequest(_Strict):
    """PATCH semantics: only sent fields change. null clears optional fields."""

    description: str | None = None
    meal_date: StrictDate | None = None
    meal_type: MealType | None = None
    portion: Portion | None = None
    memo: str | None = None

    @field_validator("description")
    @classmethod
    def _desc(cls, v: str | None) -> str | None:
        return None if v is None else normalize_description(v)

    @field_validator("memo")
    @classmethod
    def _memo(cls, v: str | None) -> str | None:
        return normalize_memo(v)

    @model_validator(mode="after")
    def _check(self) -> MealUpdateRequest:
        sent = self.model_fields_set
        if not sent:
            raise ValueError("at least one field must be provided")
        for required in ("description", "meal_date"):
            if required in sent and getattr(self, required) is None:
                raise ValueError(f"{required} cannot be null")
        return self

    def changes(self) -> dict[str, object]:
        out: dict[str, object] = {}
        for name in self.model_fields_set:
            value = getattr(self, name)
            out[name] = value.value if isinstance(value, MealType | Portion) else value
        return out


class MealOut(BaseModel):
    id: str
    description: str
    meal_date: date
    meal_type: str | None
    portion: str | None
    memo: str | None
    created_at: str
    updated_at: str

    @classmethod
    def of(cls, m: Meal) -> MealOut:
        return cls(
            id=m.id,
            description=m.description,
            meal_date=m.meal_date,
            meal_type=m.meal_type,
            portion=m.portion,
            memo=m.memo,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class MealListOut(BaseModel):
    items: list[MealOut]
    next_offset: int | None


class RecentDescriptionsOut(BaseModel):
    items: list[str]


class DailyCount(BaseModel):
    date: date
    count: int


class WeeklySummaryOut(BaseModel):
    start: date
    end: date
    days_logged: int
    daily_counts: list[DailyCount]
    portion_counts: dict[str, int]
