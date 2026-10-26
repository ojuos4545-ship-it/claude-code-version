"""Domain entities and value sets. Framework- and DB-independent."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

DESCRIPTION_MAX = 200
MEMO_MAX = 500
MAX_RANGE_DAYS = 31
# Dates before this are treated as obviously invalid input. [assumption]
MIN_MEAL_DATE = date(2000, 1, 1)


class MealType(StrEnum):
    # Declaration order is the list sort order; "none" sorts last.
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class Portion(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


MEAL_TYPE_ORDER: list[str] = [m.value for m in MealType]


PASSWORD_PROVIDER = "password"  # noqa: S105 (provider name, not a secret)


@dataclass(frozen=True)
class User:
    """Who the user is. Independent of how they log in."""

    id: str
    timezone: str
    created_at: str


@dataclass(frozen=True)
class AuthIdentity:
    """One way a user can log in (e.g. email + password)."""

    provider: str
    identifier: str
    user_id: str
    secret_hash: str | None


@dataclass(frozen=True)
class Meal:
    id: str
    user_id: str
    description: str
    meal_date: date
    meal_type: str | None
    portion: str | None
    memo: str | None
    created_at: str
    updated_at: str
