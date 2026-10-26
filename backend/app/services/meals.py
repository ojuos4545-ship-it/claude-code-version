"""Meal entry business logic. Every operation is scoped to the authenticated user."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, replace
from datetime import date, timedelta

from app.clock import Clock, local_today, to_iso
from app.domain.models import MAX_RANGE_DAYS, MIN_MEAL_DATE, Meal, Portion, User
from app.errors import Conflict, NotFound, ValidationFailed
from app.repositories.base import DuplicateError, Repository

RECENT_WINDOW_DAYS = 30  # [assumption] PRD FR-7
RECENT_LIMIT = 10  # [assumption] PRD FR-7
SUMMARY_DAYS = 7


@dataclass(frozen=True)
class MealInput:
    description: str
    meal_date: date | None = None
    meal_type: str | None = None
    portion: str | None = None
    memo: str | None = None


@dataclass(frozen=True)
class CreateResult:
    meal: Meal
    replayed: bool


@dataclass(frozen=True)
class WeeklySummary:
    start: date
    end: date
    days_logged: int
    daily_counts: list[tuple[date, int]]
    portion_counts: dict[str, int]


class MealService:
    def __init__(self, repo: Repository, clock: Clock):
        self.repo = repo
        self.clock = clock

    def _today(self, user: User) -> date:
        return local_today(self.clock(), user.timezone)

    def _check_date(self, user: User, value: date) -> None:
        if value > self._today(user):
            raise ValidationFailed.field(
                "meal_date", "future_date", "meal_date must not be later than today"
            )
        if value < MIN_MEAL_DATE:
            raise ValidationFailed.field(
                "meal_date", "too_old", f"meal_date must be on or after {MIN_MEAL_DATE}"
            )

    # ---- FR-2 ------------------------------------------------------------
    def create(self, user: User, data: MealInput, idempotency_key: str | None) -> CreateResult:
        request_hash = None
        if idempotency_key is not None:
            request_hash = _hash_input(data)
            existing = self._replay(user, idempotency_key, request_hash)
            if existing is not None:
                return CreateResult(existing, replayed=True)

        meal_date = data.meal_date or self._today(user)
        self._check_date(user, meal_date)
        now = to_iso(self.clock())
        meal = Meal(
            id=uuid.uuid4().hex,
            user_id=user.id,
            description=data.description,
            meal_date=meal_date,
            meal_type=data.meal_type,
            portion=data.portion,
            memo=data.memo,
            created_at=now,
            updated_at=now,
        )
        try:
            self.repo.insert_meal(meal, idempotency_key, request_hash)
        except DuplicateError:
            # A concurrent request with the same key won the race.
            assert idempotency_key is not None and request_hash is not None  # noqa: S101
            existing = self._replay(user, idempotency_key, request_hash)
            if existing is None:
                raise
            return CreateResult(existing, replayed=True)
        return CreateResult(meal, replayed=False)

    def _replay(self, user: User, key: str, request_hash: str) -> Meal | None:
        found = self.repo.get_meal_by_idempotency_key(user.id, key)
        if found is None:
            return None
        meal, stored_hash = found
        if stored_hash != request_hash:
            raise Conflict("Idempotency-Key was already used with a different request body.")
        return meal

    # ---- FR-5 (single) ---------------------------------------------------
    def get(self, user: User, meal_id: str) -> Meal:
        meal = self.repo.get_meal(user.id, meal_id)
        if meal is None:  # same answer for "missing" and "someone else's"
            raise NotFound("Meal not found.")
        return meal

    # ---- FR-3 ------------------------------------------------------------
    def update(self, user: User, meal_id: str, changes: dict[str, object]) -> Meal:
        with self.repo.transaction():
            current = self.get(user, meal_id)
            if "meal_date" in changes:
                self._check_date(user, changes["meal_date"])  # type: ignore[arg-type]
            updated = replace(current, **changes, updated_at=to_iso(self.clock()))
            if not self.repo.update_meal(updated):
                raise NotFound("Meal not found.")
        return updated

    # ---- FR-4 ------------------------------------------------------------
    def delete(self, user: User, meal_id: str) -> None:
        if not self.repo.delete_meal(user.id, meal_id):
            raise NotFound("Meal not found.")

    # ---- FR-5 (list) -----------------------------------------------------
    def list(
        self, user: User, start: date, end: date, limit: int, offset: int
    ) -> tuple[list[Meal], int | None]:
        if start > end:
            raise ValidationFailed.field("from", "invalid_range", "from must not be after to")
        if (end - start).days + 1 > MAX_RANGE_DAYS:
            raise ValidationFailed.field(
                "to", "range_too_long", f"range must be at most {MAX_RANGE_DAYS} days"
            )
        rows = self.repo.list_meals(user.id, start, end, limit + 1, offset)
        next_offset = offset + limit if len(rows) > limit else None
        return rows[:limit], next_offset

    # ---- FR-7 ------------------------------------------------------------
    def recent_descriptions(self, user: User) -> list[str]:
        since = to_iso(self.clock() - timedelta(days=RECENT_WINDOW_DAYS))
        return self.repo.recent_descriptions(user.id, since, RECENT_LIMIT)

    # ---- FR-8 ------------------------------------------------------------
    def weekly_summary(self, user: User, start: date) -> WeeklySummary:
        end = start + timedelta(days=SUMMARY_DAYS - 1)
        per_day: dict[date, int] = {start + timedelta(days=i): 0 for i in range(SUMMARY_DAYS)}
        portions: dict[str, int] = {p.value: 0 for p in Portion} | {"none": 0}
        for day, portion, n in self.repo.count_meals_by_date_and_portion(user.id, start, end):
            per_day[day] += n
            key = portion if portion in portions else "none"
            portions[key] += n
        return WeeklySummary(
            start=start,
            end=end,
            days_logged=sum(1 for n in per_day.values() if n > 0),
            daily_counts=sorted(per_day.items()),
            portion_counts=portions,
        )


def _hash_input(data: MealInput) -> str:
    payload = {
        "description": data.description,
        "meal_date": data.meal_date.isoformat() if data.meal_date else None,
        "meal_type": data.meal_type,
        "portion": data.portion,
        "memo": data.memo,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
