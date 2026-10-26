"""FR-7 (Should): recent distinct descriptions."""

from tests.conftest import create_meal


def _recent(client, h):
    r = client.get("/v1/meals/recent-descriptions", headers=h)
    assert r.status_code == 200
    return r.json()["items"]


def test_empty(client, alice):
    assert _recent(client, alice) == []


def test_distinct_most_recent_first(client, alice, clock):
    for text in ["rice", "  noodles ", "rice", "salad"]:
        create_meal(client, alice, description=text)
        clock.advance(minutes=1)
    assert _recent(client, alice) == ["salad", "rice", "noodles"]


def test_ordered_by_when_written_not_meal_date(client, alice, clock):
    create_meal(client, alice, description="today", meal_date="2026-10-26")
    clock.advance(minutes=1)
    create_meal(client, alice, description="backfilled", meal_date="2026-10-01")
    assert _recent(client, alice) == ["backfilled", "today"]


def test_at_most_ten(client, alice, clock):
    for i in range(12):
        create_meal(client, alice, description=f"food {i}")
        clock.advance(minutes=1)
    assert _recent(client, alice) == [f"food {i}" for i in range(11, 1, -1)]


def test_only_last_30_days(client, alice, clock):
    create_meal(client, alice, description="old")
    clock.advance(days=30, minutes=1)
    # the 30-day token TTL also passed, so log in again
    token = client.post(
        "/v1/auth/login", json={"email": "alice@example.com", "password": "correct-horse-1"}
    ).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    create_meal(client, h, description="new")
    assert _recent(client, h) == ["new"]


def test_deleted_text_hidden_unless_another_copy_remains(client, alice, clock):
    a1 = create_meal(client, alice, description="cake")
    a2 = create_meal(client, alice, description="cake")
    gone = create_meal(client, alice, description="chips")
    client.delete(f"/v1/meals/{gone['id']}", headers=alice)
    client.delete(f"/v1/meals/{a1['id']}", headers=alice)
    assert _recent(client, alice) == ["cake"]
    client.delete(f"/v1/meals/{a2['id']}", headers=alice)
    assert _recent(client, alice) == []
