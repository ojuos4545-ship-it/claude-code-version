"""FR-2: create meal entries."""

from datetime import UTC, datetime

import pytest

from tests.conftest import create_meal, signup


def test_description_only_uses_users_today_and_empty_optionals(client, alice):
    r = client.post("/v1/meals", json={"description": "  bibimbap  "}, headers=alice)
    assert r.status_code == 201
    body = r.json()
    assert set(body) == {
        "id",
        "description",
        "meal_date",
        "meal_type",
        "portion",
        "memo",
        "created_at",
        "updated_at",
    }
    assert body["id"]
    assert body["description"] == "bibimbap"
    assert body["meal_date"] == "2026-10-26"
    assert body["meal_type"] is None and body["portion"] is None and body["memo"] is None
    # response matches what was stored
    assert client.get(f"/v1/meals/{body['id']}", headers=alice).json() == body


def test_all_fields(client, alice):
    body = create_meal(
        client,
        alice,
        description="salad",
        meal_date="2026-10-25",
        meal_type="lunch",
        portion="small",
        memo="ate at desk\nfelt fine",
    )
    assert body["meal_date"] == "2026-10-25"
    assert body["meal_type"] == "lunch"
    assert body["portion"] == "small"
    assert body["memo"] == "ate at desk\nfelt fine"


@pytest.mark.parametrize(
    "payload, field",
    [
        ({}, "description"),
        ({"description": None}, "description"),
        ({"description": ""}, "description"),
        ({"description": "   \t "}, "description"),
        ({"description": "a" * 201}, "description"),
        ({"description": "two\nlines"}, "description"),
        ({"description": 123}, "description"),
        ({"description": "x", "meal_type": "brunch"}, "meal_type"),
        ({"description": "x", "meal_type": "아침"}, "meal_type"),
        ({"description": "x", "portion": "huge"}, "portion"),
        ({"description": "x", "portion": 300}, "portion"),
        ({"description": "x", "memo": "m" * 501}, "memo"),
        ({"description": "x", "meal_date": "2026-13-01"}, "meal_date"),
        ({"description": "x", "meal_date": "26-10-2026"}, "meal_date"),
        ({"description": "x", "meal_date": 1761436800}, "meal_date"),
        ({"description": "x", "kcal": 500}, "kcal"),
        ({"description": "x", "grams": 200}, "grams"),
    ],
)
def test_invalid_input_rejected_with_field_detail(client, alice, payload, field):
    r = client.post("/v1/meals", json=payload, headers=alice)
    assert r.status_code == 422, r.text
    err = r.json()["error"]
    assert err["code"] == "validation_error"
    assert field in [d["field"] for d in err["details"]]
    assert all(d["message"] for d in err["details"])
    # nothing stored
    assert client.get("/v1/meals?date=2026-10-26", headers=alice).json()["items"] == []


def test_boundary_lengths_accepted(client, alice):
    body = create_meal(client, alice, description="a" * 200, memo="m" * 500)
    assert len(body["description"]) == 200
    assert len(body["memo"]) == 500
    # length is checked after trimming
    assert (
        create_meal(client, alice, description="  " + "b" * 200 + "  ")["description"] == "b" * 200
    )


def test_blank_memo_is_stored_as_empty(client, alice):
    assert create_meal(client, alice, memo="   ")["memo"] is None


def test_malformed_json_is_validation_error(client, alice):
    r = client.post(
        "/v1/meals", content=b"{not json", headers={**alice, "Content-Type": "application/json"}
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "validation_error"


def test_future_date_rejected_past_dates_accepted(client, alice):
    r = client.post(
        "/v1/meals", json={"description": "x", "meal_date": "2026-10-27"}, headers=alice
    )
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["reason"] == "future_date"
    for d in ["2026-10-26", "2026-10-25", "2026-10-19", "2020-01-01"]:
        assert create_meal(client, alice, meal_date=d)["meal_date"] == d


def test_obviously_old_date_rejected(client, alice):
    r = client.post(
        "/v1/meals", json={"description": "x", "meal_date": "1999-12-31"}, headers=alice
    )
    assert r.status_code == 422
    assert r.json()["error"]["details"][0]["reason"] == "too_old"


def test_same_day_same_meal_type_allowed_multiple_times(client, alice):
    a = create_meal(client, alice, description="rice", meal_type="lunch")
    b = create_meal(client, alice, description="rice", meal_type="lunch")
    assert a["id"] != b["id"]
    items = client.get("/v1/meals?date=2026-10-26", headers=alice).json()["items"]
    assert len(items) == 2


def test_today_follows_user_timezone_not_server(client, clock):
    # 00:30 on 2026-10-27 in Seoul == 15:30 on 2026-10-26 UTC
    clock.set(datetime(2026, 10, 26, 15, 30, tzinfo=UTC))
    seoul = signup(client, timezone="Asia/Seoul")
    ny = signup(client, timezone="America/New_York")  # 11:30 on 2026-10-26
    assert create_meal(client, seoul)["meal_date"] == "2026-10-27"
    assert create_meal(client, ny)["meal_date"] == "2026-10-26"
    # "future" is also judged in the user's timezone
    r = client.post("/v1/meals", json={"description": "x", "meal_date": "2026-10-27"}, headers=ny)
    assert r.status_code == 422
    assert create_meal(client, seoul, meal_date="2026-10-27")["meal_date"] == "2026-10-27"


class TestIdempotency:
    def test_same_key_twice_creates_one_record(self, client, alice):
        h = {**alice, "Idempotency-Key": "req-123"}
        first = client.post("/v1/meals", json={"description": "toast"}, headers=h)
        second = client.post("/v1/meals", json={"description": "toast"}, headers=h)
        assert first.status_code == 201
        assert second.status_code == 200
        assert second.headers["idempotent-replayed"] == "true"
        assert first.json() == second.json()
        items = client.get("/v1/meals?date=2026-10-26", headers=alice).json()["items"]
        assert len(items) == 1

    def test_same_key_different_body_conflicts(self, client, alice):
        h = {**alice, "Idempotency-Key": "req-1"}
        assert client.post("/v1/meals", json={"description": "a"}, headers=h).status_code == 201
        r = client.post("/v1/meals", json={"description": "b"}, headers=h)
        assert r.status_code == 409
        assert len(client.get("/v1/meals?date=2026-10-26", headers=alice).json()["items"]) == 1

    def test_keys_are_scoped_per_user(self, client, alice, bob):
        a = client.post(
            "/v1/meals", json={"description": "a"}, headers={**alice, "Idempotency-Key": "k"}
        )
        b = client.post(
            "/v1/meals", json={"description": "a"}, headers={**bob, "Idempotency-Key": "k"}
        )
        assert a.status_code == b.status_code == 201
        assert a.json()["id"] != b.json()["id"]

    def test_without_key_each_request_creates(self, client, alice):
        create_meal(client, alice, description="same")
        create_meal(client, alice, description="same")
        assert len(client.get("/v1/meals?date=2026-10-26", headers=alice).json()["items"]) == 2

    def test_invalid_key_rejected(self, client, alice):
        r = client.post(
            "/v1/meals", json={"description": "a"}, headers={**alice, "Idempotency-Key": "a" * 101}
        )
        assert r.status_code == 422
