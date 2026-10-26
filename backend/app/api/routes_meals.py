from __future__ import annotations

import re
from datetime import date

from fastapi import APIRouter, Depends, Header, Query, Response, status

from app.api.deps import current_user, get_meal_service
from app.api.schemas import (
    DailyCount,
    MealCreateRequest,
    MealListOut,
    MealOut,
    MealUpdateRequest,
    RecentDescriptionsOut,
    WeeklySummaryOut,
)
from app.domain.models import User
from app.errors import ValidationFailed
from app.services.meals import MealInput, MealService

router = APIRouter(prefix="/v1")

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_IDEM_KEY = re.compile(r"^[A-Za-z0-9_.:-]{1,100}$")
DEFAULT_PAGE, MAX_PAGE = 100, 200


def _parse_date(field: str, raw: str) -> date:
    if not _DATE.match(raw):
        raise ValidationFailed.field(field, "invalid_date", "must be a date in YYYY-MM-DD format")
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise ValidationFailed.field(
            field, "invalid_date", "is not a valid calendar date"
        ) from None


@router.post("/meals", status_code=status.HTTP_201_CREATED, response_model=MealOut)
def create_meal(
    body: MealCreateRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None),
    user: User = Depends(current_user),
    meals: MealService = Depends(get_meal_service),
):
    if idempotency_key is not None and not _IDEM_KEY.match(idempotency_key):
        raise ValidationFailed.field(
            "Idempotency-Key", "invalid", "must be 1-100 chars of [A-Za-z0-9_.:-]"
        )
    data = MealInput(
        description=body.description,
        meal_date=body.meal_date,
        meal_type=body.meal_type.value if body.meal_type else None,
        portion=body.portion.value if body.portion else None,
        memo=body.memo,
    )
    result = meals.create(user, data, idempotency_key)
    if result.replayed:
        response.status_code = status.HTTP_200_OK
        response.headers["Idempotent-Replayed"] = "true"
    return MealOut.of(result.meal)


@router.get("/meals", response_model=MealListOut)
def list_meals(
    date_: str | None = Query(default=None, alias="date"),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    limit: int = Query(default=DEFAULT_PAGE, ge=1, le=MAX_PAGE),
    offset: int = Query(default=0, ge=0, le=100_000),
    user: User = Depends(current_user),
    meals: MealService = Depends(get_meal_service),
):
    if date_ is not None:
        if from_ is not None or to is not None:
            raise ValidationFailed.field("date", "conflict", "use either date or from/to, not both")
        start = end = _parse_date("date", date_)
    elif from_ is not None and to is not None:
        start, end = _parse_date("from", from_), _parse_date("to", to)
    else:
        raise ValidationFailed.field("date", "missing", "provide date, or both from and to")
    items, next_offset = meals.list(user, start, end, limit, offset)
    return MealListOut(items=[MealOut.of(m) for m in items], next_offset=next_offset)


# Declared before /meals/{meal_id} so "recent" is not captured as an id.
@router.get("/meals/recent-descriptions", response_model=RecentDescriptionsOut)
def recent_descriptions(
    user: User = Depends(current_user), meals: MealService = Depends(get_meal_service)
):
    return RecentDescriptionsOut(items=meals.recent_descriptions(user))


@router.get("/meals/{meal_id}", response_model=MealOut)
def get_meal(
    meal_id: str, user: User = Depends(current_user), meals: MealService = Depends(get_meal_service)
):
    return MealOut.of(meals.get(user, meal_id))


@router.patch("/meals/{meal_id}", response_model=MealOut)
def update_meal(
    meal_id: str,
    body: MealUpdateRequest,
    user: User = Depends(current_user),
    meals: MealService = Depends(get_meal_service),
):
    return MealOut.of(meals.update(user, meal_id, body.changes()))


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meal(
    meal_id: str, user: User = Depends(current_user), meals: MealService = Depends(get_meal_service)
):
    meals.delete(user, meal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/summaries/weekly", response_model=WeeklySummaryOut)
def weekly_summary(
    start: str = Query(),
    user: User = Depends(current_user),
    meals: MealService = Depends(get_meal_service),
):
    s = meals.weekly_summary(user, _parse_date("start", start))
    return WeeklySummaryOut(
        start=s.start,
        end=s.end,
        days_logged=s.days_logged,
        daily_counts=[DailyCount(date=d, count=n) for d, n in s.daily_counts],
        portion_counts=s.portion_counts,
    )
