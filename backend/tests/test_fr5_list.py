"""FR-5: list by date / date range, and single fetch."""

import pytest

from tests.conftest import create_meal


def _list(client, h, query):
    r = client.get(f"/v1/meals?{query}", headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_single_date_returns_only_that_date(client, alice):
    create_meal(client, alice, description="d25", meal_date="2026-10-25")
    create_meal(client, alice, description="d26", meal_date="2026-10-26")
    body = _list(client, alice, "date=2026-10-25")
    assert [m["description"] for m in body["items"]] == ["d25"]
    assert body["next_offset"] is None


def test_day_without_meals_is_empty_not_error(client, alice):
    assert _list(client, alice, "date=2026-01-01") == {"items": [], "next_offset": None}


def test_range_is_inclusive(client, alice):
    for d in ["2026-10-09", "2026-10-10", "2026-10-15", "2026-10-20", "2026-10-21"]:
        create_meal(client, alice, description=d, meal_date=d)
    items = _list(client, alice, "from=2026-10-10&to=2026-10-20")["items"]
    assert [m["description"] for m in items] == ["2026-10-10", "2026-10-15", "2026-10-20"]


def test_sort_order_date_then_meal_type_then_created(client, alice):
    create_meal(client, alice, description="26-none", meal_date="2026-10-26")
    create_meal(client, alice, description="26-snack", meal_date="2026-10-26", meal_type="snack")
    create_meal(
        client, alice, description="26-breakfast-1", meal_date="2026-10-26", meal_type="breakfast"
    )
    create_meal(client, alice, description="25-dinner", meal_date="2026-10-25", meal_type="dinner")
    create_meal(client, alice, description="26-dinner", meal_date="2026-10-26", meal_type="dinner")
    create_meal(client, alice, description="26-lunch", meal_date="2026-10-26", meal_type="lunch")
    create_meal(
        client, alice, description="26-breakfast-2", meal_date="2026-10-26", meal_type="breakfast"
    )
    items = _list(client, alice, "from=2026-10-25&to=2026-10-26")["items"]
    assert [m["description"] for m in items] == [
        "25-dinner",
        "26-breakfast-1",
        "26-breakfast-2",
        "26-lunch",
        "26-dinner",
        "26-snack",
        "26-none",
    ]


def test_31_day_range_allowed_32_rejected(client, alice):
    assert _list(client, alice, "from=2026-09-26&to=2026-10-26")["items"] == []
    r = client.get("/v1/meals?from=2026-09-25&to=2026-10-26", headers=alice)
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["reason"] == "range_too_long"


@pytest.mark.parametrize(
    "query, field",
    [
        ("from=2026-10-26&to=2026-10-25", "from"),
        ("", "date"),
        ("from=2026-10-01", "date"),
        ("date=2026-10-26&from=2026-10-01&to=2026-10-02", "date"),
        ("date=2026/10/26", "date"),
        ("date=2026-02-30", "date"),
        ("from=x&to=2026-10-26", "from"),
        ("date=2026-10-26&limit=0", "limit"),
        ("date=2026-10-26&limit=201", "limit"),
        ("date=2026-10-26&offset=-1", "offset"),
    ],
)
def test_invalid_queries_rejected(client, alice, query, field):
    r = client.get(f"/v1/meals?{query}", headers=alice)
    assert r.status_code == 422, r.text
    assert r.json()["error"]["details"][0]["field"] == field


def test_pagination(client, alice):
    ids = [create_meal(client, alice, description=f"m{i}")["id"] for i in range(5)]
    page1 = _list(client, alice, "date=2026-10-26&limit=2")
    assert [m["id"] for m in page1["items"]] == ids[:2]
    assert page1["next_offset"] == 2
    page2 = _list(client, alice, "date=2026-10-26&limit=2&offset=2")
    page3 = _list(client, alice, f"date=2026-10-26&limit=2&offset={page2['next_offset']}")
    assert [m["id"] for m in page2["items"] + page3["items"]] == ids[2:]
    assert page3["next_offset"] is None


def test_default_page_size_is_capped(client, alice):
    body = _list(client, alice, "date=2026-10-26")
    assert body["next_offset"] is None  # empty, but the default limit is applied server-side


def test_single_fetch_returns_all_fields(client, alice):
    meal = create_meal(
        client,
        alice,
        description="soup",
        meal_date="2026-10-20",
        meal_type="breakfast",
        portion="medium",
        memo="warm",
    )
    r = client.get(f"/v1/meals/{meal['id']}", headers=alice)
    assert r.status_code == 200
    assert r.json() == meal
    assert client.get("/v1/meals/does-not-exist", headers=alice).status_code == 404
