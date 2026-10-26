"""FR-3: update meal entries."""

import pytest

from tests.conftest import create_meal

FULL = {
    "description": "pasta",
    "meal_date": "2026-10-25",
    "meal_type": "dinner",
    "portion": "large",
    "memo": "with friends",
}


def test_partial_update_keeps_other_fields(client, alice):
    meal = create_meal(client, alice, **FULL)
    r = client.patch(f"/v1/meals/{meal['id']}", json={"portion": "medium"}, headers=alice)
    assert r.status_code == 200
    body = r.json()
    assert body["portion"] == "medium"
    for k in ("description", "meal_date", "meal_type", "memo", "id", "created_at"):
        assert body[k] == meal[k]
    assert client.get(f"/v1/meals/{meal['id']}", headers=alice).json() == body


def test_update_every_field(client, alice):
    meal = create_meal(client, alice)
    changes = {**FULL, "description": "  ramen  "}
    body = client.patch(f"/v1/meals/{meal['id']}", json=changes, headers=alice).json()
    assert body["description"] == "ramen"
    assert body["meal_date"] == "2026-10-25"
    assert body["meal_type"] == "dinner"


def test_optional_fields_can_be_cleared(client, alice):
    meal = create_meal(client, alice, **FULL)
    r = client.patch(
        f"/v1/meals/{meal['id']}",
        json={"meal_type": None, "portion": None, "memo": None},
        headers=alice,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["meal_type"] is None and body["portion"] is None and body["memo"] is None
    assert body["description"] == "pasta"


@pytest.mark.parametrize(
    "payload, field",
    [
        ({"description": None}, "body"),
        ({"description": "  "}, "description"),
        ({"description": "a" * 201}, "description"),
        ({"meal_type": "brunch"}, "meal_type"),
        ({"portion": "xl"}, "portion"),
        ({"memo": "m" * 501}, "memo"),
        ({"meal_date": None}, "body"),
        ({"meal_date": "2026-10-32"}, "meal_date"),
        ({"meal_date": "2026-10-27"}, "meal_date"),  # future
        ({"kcal": 100}, "kcal"),
        ({}, "body"),
    ],
)
def test_update_validation_same_as_create(client, alice, payload, field):
    meal = create_meal(client, alice, **FULL)
    r = client.patch(f"/v1/meals/{meal['id']}", json=payload, headers=alice)
    assert r.status_code == 422, r.text
    assert field in [d["field"] for d in r.json()["error"]["details"]]
    assert client.get(f"/v1/meals/{meal['id']}", headers=alice).json() == meal


def test_updated_at_changes_created_at_does_not(client, alice, clock):
    meal = create_meal(client, alice)
    clock.advance(minutes=5)
    body = client.patch(f"/v1/meals/{meal['id']}", json={"memo": "later"}, headers=alice).json()
    assert body["created_at"] == meal["created_at"]
    assert body["updated_at"] > meal["updated_at"]


def test_update_missing_or_foreign_meal_is_404(client, alice, bob):
    meal = create_meal(client, alice)
    assert client.patch("/v1/meals/nope", json={"memo": "x"}, headers=alice).status_code == 404
    r = client.patch(f"/v1/meals/{meal['id']}", json={"memo": "x"}, headers=bob)
    assert r.status_code == 404
    assert client.get(f"/v1/meals/{meal['id']}", headers=alice).json()["memo"] is None
